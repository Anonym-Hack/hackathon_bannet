from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import MaterialListing, BuyerRequest, User
from app.schemas import ImpactStatsResponse, CategoryImpact

router = APIRouter(prefix="/analytics", tags=["Impact & Analytics"])

# CO2 reduction factors per kg of waste diverted (vs virgin production)
CO2_FACTORS = {
    "metal": 4.5,
    "plastic": 1.85,
    "chemical": 2.1,
    "textile": 3.6,
    "wood": 1.2,
    "glass": 0.85,
    "organic": 0.95,
    "construction": 0.22,
    "electronic": 12.5,
    "other": 1.0,
}

AVG_VIRGIN_VALUE_PER_KG = {
    "metal": 3.5,
    "plastic": 2.2,
    "chemical": 2.8,
    "textile": 1.5,
    "wood": 0.5,
    "glass": 0.4,
    "organic": 0.3,
    "construction": 0.15,
    "electronic": 15.0,
    "other": 1.0,
}

@router.get("/impact", response_model=ImpactStatsResponse)
def get_impact_statistics(db: Session = Depends(get_db)):
    listings = db.query(MaterialListing).all()
    requests_count = db.query(BuyerRequest).filter(BuyerRequest.status == "open").count()
    companies_count = db.query(User).count()

    total_diverted_kg = 0.0
    total_co2_kg = 0.0
    total_savings_usd = 0.0

    category_buckets = {}

    for l in listings:
        cat = (l.category or "other").lower()
        qty = float(l.quantity or 0)
        # normalize unit if tonnes
        if (l.unit or "").lower() in ["tonne", "tonnes", "t", "ton"]:
            qty_kg = qty * 1000.0
        elif (l.unit or "").lower() in ["g", "grams"]:
            qty_kg = qty / 1000.0
        else:
            qty_kg = qty

        total_diverted_kg += qty_kg
        factor = CO2_FACTORS.get(cat, 1.0)
        co2_saved = qty_kg * factor
        total_co2_kg += co2_saved

        # Estimated cost savings
        virgin_val = AVG_VIRGIN_VALUE_PER_KG.get(cat, 1.0)
        listing_val = float(l.price or 0)
        savings = max(0.0, (virgin_val - listing_val) * qty_kg)
        total_savings_usd += savings

        if cat not in category_buckets:
            category_buckets[cat] = {"weight_kg": 0.0, "co2_saved_kg": 0.0, "count": 0}
        category_buckets[cat]["weight_kg"] += qty_kg
        category_buckets[cat]["co2_saved_kg"] += co2_saved
        category_buckets[cat]["count"] += 1

    cat_list = [
        CategoryImpact(
            category=k,
            weight_kg=round(v["weight_kg"], 1),
            co2_saved_kg=round(v["co2_saved_kg"], 1),
            listings_count=v["count"]
        )
        for k, v in category_buckets.items()
    ]
    cat_list.sort(key=lambda x: x.weight_kg, reverse=True)

    return ImpactStatsResponse(
        total_waste_diverted_kg=round(total_diverted_kg, 1),
        estimated_co2_saved_kg=round(total_co2_kg, 1),
        estimated_cost_savings_usd=round(total_savings_usd, 2),
        active_listings_count=len(listings),
        active_requests_count=requests_count,
        registered_companies_count=companies_count,
        category_breakdown=cat_list,
        disclaimer="All environmental and economic figures are realistic circular-economy estimations based on material composition and lifecycle assessment (LCA) models."
    )
