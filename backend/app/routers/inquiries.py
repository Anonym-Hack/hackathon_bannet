from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database import get_db
from app.models import Inquiry, Message, MaterialListing, User
from app.schemas import InquiryCreate, InquiryResponse, MessageCreate, MessageResponse
from app.auth import get_current_user

router = APIRouter(prefix="/inquiries", tags=["Inquiries & Chat"])

@router.get("/unread-count")
def get_total_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inquiries = db.query(Inquiry).filter(
        or_(Inquiry.buyer_id == current_user.id, Inquiry.supplier_id == current_user.id)
    ).all()
    inquiry_ids = [inq.id for inq in inquiries]

    if not inquiry_ids:
        return {"unread_count": 0}

    unread = db.query(Message).filter(
        Message.inquiry_id.in_(inquiry_ids),
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).count()

    return {"unread_count": unread}

@router.get("", response_model=List[InquiryResponse])
def get_user_inquiries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inquiries = db.query(Inquiry).filter(
        or_(Inquiry.buyer_id == current_user.id, Inquiry.supplier_id == current_user.id)
    ).order_by(desc(Inquiry.updated_at)).all()

    response_list = []
    for inq in inquiries:
        unread = db.query(Message).filter(
            Message.inquiry_id == inq.id,
            Message.sender_id != current_user.id,
            Message.is_read == False
        ).count()

        latest_msg = db.query(Message).filter(
            Message.inquiry_id == inq.id
        ).order_by(desc(Message.created_at)).first()

        resp = InquiryResponse(
            id=inq.id,
            listing_id=inq.listing_id,
            buyer_id=inq.buyer_id,
            supplier_id=inq.supplier_id,
            subject=inq.subject,
            status=inq.status,
            created_at=inq.created_at,
            updated_at=inq.updated_at,
            listing_title=inq.listing.title if inq.listing else "Listing",
            buyer_company=inq.buyer.company_name if inq.buyer else "Buyer",
            supplier_company=inq.supplier.company_name if inq.supplier else "Supplier",
            unread_count=unread,
            latest_message=latest_msg.content if latest_msg else None,
            messages=[]
        )
        response_list.append(resp)

    return response_list

@router.get("/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry_thread(
    inquiry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inq = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inq:
        raise HTTPException(status_code=404, detail="Inquiry thread not found.")

    if inq.buyer_id != current_user.id and inq.supplier_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this inquiry.")

    # Mark all incoming messages as read
    incoming_msgs = db.query(Message).filter(
        Message.inquiry_id == inq.id,
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).all()
    for m in incoming_msgs:
        m.is_read = True
    if incoming_msgs:
        db.commit()

    all_msgs = db.query(Message).filter(Message.inquiry_id == inq.id).order_by(Message.created_at).all()
    msg_responses = []
    for m in all_msgs:
        msg_responses.append(
            MessageResponse(
                id=m.id,
                inquiry_id=m.inquiry_id,
                sender_id=m.sender_id,
                content=m.content,
                is_read=m.is_read,
                created_at=m.created_at,
                sender_company=m.sender.company_name if m.sender else None,
                sender_role=m.sender.role if m.sender else None
            )
        )

    return InquiryResponse(
        id=inq.id,
        listing_id=inq.listing_id,
        buyer_id=inq.buyer_id,
        supplier_id=inq.supplier_id,
        subject=inq.subject,
        status=inq.status,
        created_at=inq.created_at,
        updated_at=inq.updated_at,
        listing_title=inq.listing.title if inq.listing else "Listing",
        buyer_company=inq.buyer.company_name if inq.buyer else "Buyer",
        supplier_company=inq.supplier.company_name if inq.supplier else "Supplier",
        unread_count=0,
        latest_message=all_msgs[-1].content if all_msgs else None,
        messages=msg_responses
    )

@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(
    inquiry_in: InquiryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    listing = db.query(MaterialListing).filter(MaterialListing.id == inquiry_in.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Material listing not found.")

    if listing.supplier_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot send an inquiry on your own listing.")

    new_inquiry = Inquiry(
        listing_id=listing.id,
        buyer_id=current_user.id,
        supplier_id=listing.supplier_id,
        subject=inquiry_in.subject.strip(),
        status="open"
    )
    db.add(new_inquiry)
    db.commit()
    db.refresh(new_inquiry)

    first_msg = Message(
        inquiry_id=new_inquiry.id,
        sender_id=current_user.id,
        content=inquiry_in.message.strip(),
        is_read=False
    )
    db.add(first_msg)
    db.commit()
    db.refresh(first_msg)

    msg_resp = MessageResponse(
        id=first_msg.id,
        inquiry_id=first_msg.inquiry_id,
        sender_id=first_msg.sender_id,
        content=first_msg.content,
        is_read=first_msg.is_read,
        created_at=first_msg.created_at,
        sender_company=current_user.company_name,
        sender_role=current_user.role
    )

    return InquiryResponse(
        id=new_inquiry.id,
        listing_id=new_inquiry.listing_id,
        buyer_id=new_inquiry.buyer_id,
        supplier_id=new_inquiry.supplier_id,
        subject=new_inquiry.subject,
        status=new_inquiry.status,
        created_at=new_inquiry.created_at,
        updated_at=new_inquiry.updated_at,
        listing_title=listing.title,
        buyer_company=current_user.company_name,
        supplier_company=listing.supplier.company_name if listing.supplier else "Supplier",
        unread_count=0,
        latest_message=first_msg.content,
        messages=[msg_resp]
    )

@router.post("/{inquiry_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def post_reply(
    inquiry_id: int,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inq = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inq:
        raise HTTPException(status_code=404, detail="Inquiry thread not found.")

    if inq.buyer_id != current_user.id and inq.supplier_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to post in this inquiry.")

    new_msg = Message(
        inquiry_id=inq.id,
        sender_id=current_user.id,
        content=msg_in.content.strip(),
        is_read=False
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    return MessageResponse(
        id=new_msg.id,
        inquiry_id=new_msg.inquiry_id,
        sender_id=new_msg.sender_id,
        content=new_msg.content,
        is_read=new_msg.is_read,
        created_at=new_msg.created_at,
        sender_company=current_user.company_name,
        sender_role=current_user.role
    )
