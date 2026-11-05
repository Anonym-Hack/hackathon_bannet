import json
import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.database import get_db
from app.models import MaterialListing, User
from app.schemas import ListingResponse, ListingCreate, ListingUpdate
from app.auth import get_current_user, get_optional_user
from app.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from app.ai_service import analyze_material, rule_based_analyze

router = APIRouter(prefix="/listings", tags=["Material Listings"])

@router.get("", response_model=List[ListingResponse])
def get_listings(
    q: Optional[str] = Query(None, description="Search keyword in title, description, or composition"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location: Optional[str] = Query(None, description="Filter by city or location"),
    min_quantity: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    free_only: Optional[bool] = Query(False),
    sort_by: Optional[str] = Query("newest", description="newest, price_asc, price_desc, sustainability, quantity_desc"),
    status_filter: Optional[str] = Query("available", description="available, all, reserved, completed"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier user ID"),
    db: Session = Depends(get_db)
):
    query = db.query(MaterialListing)

    if supplier_id:
        query = query.filter(MaterialListing.supplier_id == supplier_id)
    elif status_filter != "all":
        query = query.filter(MaterialListing.availability_status == status_filter)

    if category and category.lower() != "all":
        query = query.filter(MaterialListing.category == category.lower())

    if location:
        query = query.filter(MaterialListing.location.ilike(f"%{location.strip()}%"))

    if min_quantity is not None:
        query = query.filter(MaterialListing.quantity >= min_quantity)

    if free_only:
        query = query.filter(or_(MaterialListing.price_type == "free", MaterialListing.price == 0))
    elif max_price is not None:
        query = query.filter(MaterialListing.price <= max_price)

    if q:
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                MaterialListing.title.ilike(search_term),
                MaterialListing.description.ilike(search_term),
                MaterialListing.ai_material_name.ilike(search_term),
                MaterialListing.ai_composition.ilike(search_term),
                MaterialListing.location.ilike(search_term),
                MaterialListing.category.ilike(search_term),
            )
        )

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(asc(MaterialListing.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(MaterialListing.price))
    elif sort_by == "sustainability":
        query = query.order_by(desc(MaterialListing.ai_sustainability_score))
    elif sort_by == "quantity_desc":
        query = query.order_by(desc(MaterialListing.quantity))
    else:  # newest
        query = query.order_by(desc(MaterialListing.created_at))

    listings = query.all()
    return [ListingResponse.model_validate(l) for l in listings]

@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(MaterialListing).filter(MaterialListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Material listing not found.")
    return ListingResponse.model_validate(listing)

@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form("kg"),
    price_type: str = Form("fixed"),
    price: float = Form(0.0),
    location: str = Form(...),
    availability_status: str = Form("available"),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only suppliers or demo users can post listings
    if current_user.role != "Supplier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only registered Suppliers can create material listings."
        )

    saved_image_url = None
    saved_image_path = None

    if image and image.filename:
        # Validate file extension
        ext = Path(image.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        content = await image.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of 5 MB."
            )

        unique_filename = f"{uuid.uuid4().hex}{ext}"
        saved_image_path = UPLOAD_DIR / unique_filename
        with open(saved_image_path, "wb") as f:
            f.write(content)
        
        saved_image_url = f"/api/uploads/{unique_filename}"

    # Perform AI Material Analysis
    ai_result = await analyze_material(
        title=title,
        description=description,
        image_path=saved_image_path,
        category_hint=category
    )

    new_listing = MaterialListing(
        supplier_id=current_user.id,
        title=title.strip(),
        description=description.strip(),
        category=ai_result.category or category.lower(),
        quantity=quantity,
        unit=unit.strip(),
        price_type=price_type,
        price=price if price_type != "free" else 0.0,
        location=location.strip(),
        availability_status=availability_status,
        image_url=saved_image_url,
        ai_material_name=ai_result.material_name,
        ai_composition=ai_result.composition,
        ai_condition=ai_result.condition,
        ai_reuse_applications_json=json.dumps(ai_result.reuse_applications),
        ai_target_industries_json=json.dumps(ai_result.target_industries),
        ai_handling_notes=ai_result.handling_notes,
        ai_sustainability_score=ai_result.sustainability_score,
        ai_confidence=ai_result.confidence,
        ai_is_demo_mode=ai_result.is_demo_mode,
        is_hazardous=ai_result.is_hazardous
    )

    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    return ListingResponse.model_validate(new_listing)

@router.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    listing_update: ListingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    listing = db.query(MaterialListing).filter(MaterialListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Material listing not found.")
    
    if listing.supplier_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this listing.")

    update_data = listing_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(listing, field, val)

    # If title or description changed, re-run rule analysis for updated tags
    if "title" in update_data or "description" in update_data:
        rule_res = rule_based_analyze(listing.title, listing.description, listing.category)
        listing.ai_material_name = rule_res.material_name
        listing.ai_reuse_applications_json = json.dumps(rule_res.reuse_applications)
        listing.ai_target_industries_json = json.dumps(rule_res.target_industries)
        listing.ai_handling_notes = rule_res.handling_notes
        listing.ai_sustainability_score = rule_res.sustainability_score
        listing.is_hazardous = rule_res.is_hazardous

    db.commit()
    db.refresh(listing)
    return ListingResponse.model_validate(listing)

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    listing = db.query(MaterialListing).filter(MaterialListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Material listing not found.")
    
    if listing.supplier_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this listing.")

    # Remove image file if stored locally
    if listing.image_url and listing.image_url.startswith("/api/uploads/"):
        filename = listing.image_url.split("/")[-1]
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass

    db.delete(listing)
    db.commit()
    return None
