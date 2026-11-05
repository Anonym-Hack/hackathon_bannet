from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import BuyerRequest, User
from app.schemas import BuyerRequestCreate, BuyerRequestUpdate, BuyerRequestResponse
from app.auth import get_current_user

router = APIRouter(prefix="/requests", tags=["Buyer Requests"])

@router.get("", response_model=List[BuyerRequestResponse])
def get_requests(
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    status_filter: Optional[str] = Query("open"),
    buyer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(BuyerRequest)

    if buyer_id:
        query = query.filter(BuyerRequest.buyer_id == buyer_id)
    elif status_filter != "all":
        query = query.filter(BuyerRequest.status == status_filter)

    if category and category.lower() != "all":
        query = query.filter(BuyerRequest.category == category.lower())

    if location:
        query = query.filter(BuyerRequest.location.ilike(f"%{location.strip()}%"))

    requests = query.order_by(desc(BuyerRequest.created_at)).all()
    return [BuyerRequestResponse.model_validate(r) for r in requests]

@router.get("/{request_id}", response_model=BuyerRequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    req = db.query(BuyerRequest).filter(BuyerRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Buyer request not found.")
    return BuyerRequestResponse.model_validate(req)

@router.post("", response_model=BuyerRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    request_in: BuyerRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "Buyer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered Buyers can post material requests."
        )

    new_req = BuyerRequest(
        buyer_id=current_user.id,
        material_name=request_in.material_name.strip(),
        category=request_in.category.lower().strip(),
        quantity_needed=request_in.quantity_needed,
        unit=request_in.unit.strip(),
        location=request_in.location.strip(),
        use_case=request_in.use_case.strip() if request_in.use_case else None,
        status="open"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return BuyerRequestResponse.model_validate(new_req)

@router.put("/{request_id}", response_model=BuyerRequestResponse)
def update_request(
    request_id: int,
    request_in: BuyerRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(BuyerRequest).filter(BuyerRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Buyer request not found.")

    if req.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this request.")

    update_data = request_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(req, field, val)

    db.commit()
    db.refresh(req)
    return BuyerRequestResponse.model_validate(req)

@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(BuyerRequest).filter(BuyerRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Buyer request not found.")

    if req.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this request.")

    db.delete(req)
    db.commit()
    return None
