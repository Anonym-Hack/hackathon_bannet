from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MaterialListing, BuyerRequest, User
from app.schemas import MatchResult, ListingResponse, BuyerRequestResponse
from app.matching_service import compute_match_score
from app.auth import get_optional_user

router = APIRouter(prefix="/matches", tags=["AI Matching"])

@router.get("/for-listing/{listing_id}", response_model=List[MatchResult])
def get_matches_for_listing(
    listing_id: int,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    listing = db.query(MaterialListing).filter(MaterialListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Material listing not found.")

    requests = db.query(BuyerRequest).filter(BuyerRequest.status == "open").all()
    results = []
    for req in requests:
        score, why = compute_match_score(listing, req)
        results.append(
            MatchResult(
                match_score=score,
                why_matched=why,
                listing=ListingResponse.model_validate(listing),
                request=BuyerRequestResponse.model_validate(req)
            )
        )

    results.sort(key=lambda x: x.match_score, reverse=True)
    return results[:limit]

@router.get("/for-request/{request_id}", response_model=List[MatchResult])
def get_matches_for_request(
    request_id: int,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    req = db.query(BuyerRequest).filter(BuyerRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Buyer request not found.")

    listings = db.query(MaterialListing).filter(MaterialListing.availability_status == "available").all()
    results = []
    for l in listings:
        score, why = compute_match_score(l, req)
        results.append(
            MatchResult(
                match_score=score,
                why_matched=why,
                listing=ListingResponse.model_validate(l),
                request=BuyerRequestResponse.model_validate(req)
            )
        )

    results.sort(key=lambda x: x.match_score, reverse=True)
    return results[:limit]

@router.get("/recommendations", response_model=List[MatchResult])
def get_recommended_matches(
    limit: int = Query(12, ge=1, le=50),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    results = []

    if current_user and current_user.role == "Supplier":
        # Match supplier's listings against all open buyer requests
        my_listings = db.query(MaterialListing).filter(
            MaterialListing.supplier_id == current_user.id,
            MaterialListing.availability_status == "available"
        ).all()
        open_requests = db.query(BuyerRequest).filter(BuyerRequest.status == "open").all()
        for l in my_listings:
            for r in open_requests:
                score, why = compute_match_score(l, r)
                if score >= 40:
                    results.append(
                        MatchResult(
                            match_score=score,
                            why_matched=why,
                            listing=ListingResponse.model_validate(l),
                            request=BuyerRequestResponse.model_validate(r)
                        )
                    )

    elif current_user and current_user.role == "Buyer":
        # Match buyer's requests against all available listings
        my_requests = db.query(BuyerRequest).filter(
            BuyerRequest.buyer_id == current_user.id,
            BuyerRequest.status == "open"
        ).all()
        available_listings = db.query(MaterialListing).filter(MaterialListing.availability_status == "available").all()
        for r in my_requests:
            for l in available_listings:
                score, why = compute_match_score(l, r)
                if score >= 40:
                    results.append(
                        MatchResult(
                            match_score=score,
                            why_matched=why,
                            listing=ListingResponse.model_validate(l),
                            request=BuyerRequestResponse.model_validate(r)
                        )
                    )

    # If no user-specific matches or user has no listings/requests, compute top global matches across the marketplace
    if not results:
        listings = db.query(MaterialListing).filter(MaterialListing.availability_status == "available").limit(20).all()
        requests = db.query(BuyerRequest).filter(BuyerRequest.status == "open").limit(20).all()
        for l in listings:
            for r in requests:
                score, why = compute_match_score(l, r)
                if score >= 45:
                    results.append(
                        MatchResult(
                            match_score=score,
                            why_matched=why,
                            listing=ListingResponse.model_validate(l),
                            request=BuyerRequestResponse.model_validate(r)
                        )
                    )

    results.sort(key=lambda x: x.match_score, reverse=True)
    return results[:limit]
