import re
from typing import List, Tuple, Dict, Any
from app.models import MaterialListing, BuyerRequest

def tokenize(text: str) -> set:
    """Extract clean lower-case alphanumeric word tokens."""
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    # Exclude common stopwords
    stopwords = {"and", "for", "with", "the", "material", "industrial", "grade", "clean", "need", "looking", "waste"}
    return {w for w in words if w not in stopwords}

def compute_match_score(listing: MaterialListing, request: BuyerRequest) -> Tuple[int, List[str]]:
    """
    Compute a 0 - 100 match score and generate explanatory reasons why they match.
    Considers:
    - Category match (up to 35 pts)
    - Keyword overlap between title/desc and request material/use case (up to 25 pts)
    - AI-suggested industries vs buyer use case (up to 20 pts)
    - Location synergy (up to 10 pts)
    - Quantity compatibility (up to 10 pts)
    """
    score = 0
    reasons = []

    # 1. Category Match (35 pts)
    listing_cat = (listing.category or "").strip().lower()
    req_cat = (request.category or "").strip().lower()
    if listing_cat and req_cat:
        if listing_cat == req_cat:
            score += 35
            reasons.append(f"Direct category match: {listing.category.capitalize()}")
        elif listing_cat in req_cat or req_cat in listing_cat:
            score += 20
            reasons.append(f"Related material category: {listing.category.capitalize()}")

    # 2. Keyword & Text Similarity (25 pts)
    listing_tokens = tokenize(f"{listing.title} {listing.description} {listing.ai_material_name or ''} {listing.ai_composition or ''}")
    request_tokens = tokenize(f"{request.material_name} {request.use_case or ''}")
    
    overlap = listing_tokens.intersection(request_tokens)
    if overlap:
        kw_pts = min(25, len(overlap) * 7)
        score += kw_pts
        matched_keywords = list(overlap)[:3]
        reasons.append(f"Keyword alignment on: {', '.join(matched_keywords)}")

    # 3. AI Target Industries & Reuse Applications (20 pts)
    industries = listing.ai_target_industries or []
    applications = listing.ai_reuse_applications or []
    req_text = f"{request.use_case or ''} {request.material_name}".lower()
    
    ind_matched = False
    for ind in industries:
        ind_words = tokenize(ind)
        if ind_words and any(w in req_text for w in ind_words):
            score += 20
            reasons.append(f"AI Industry Fit: Ideal for {ind}")
            ind_matched = True
            break
            
    if not ind_matched:
        for app in applications:
            app_words = tokenize(app)
            if app_words and any(w in req_text for w in app_words):
                score += 15
                reasons.append(f"AI Reuse Potential: {app}")
                break

    # 4. Location Proximity (10 pts)
    listing_loc = (listing.location or "").strip().lower()
    req_loc = (request.location or "").strip().lower()
    if listing_loc and req_loc:
        if listing_loc == req_loc or listing_loc in req_loc or req_loc in listing_loc:
            score += 10
            reasons.append(f"Location proximity in {listing.location}")
        else:
            # Common country / state shorthand check
            score += 4
            reasons.append("Domestic transport distance viable")

    # 5. Quantity Compatibility (10 pts)
    l_qty = float(listing.quantity or 0)
    r_qty = float(request.quantity_needed or 0)
    if l_qty > 0 and r_qty > 0:
        ratio = l_qty / r_qty
        if 0.5 <= ratio <= 2.0:
            score += 10
            reasons.append(f"Optimal quantity match ({listing.quantity:g} {listing.unit} vs {request.quantity_needed:g} {request.unit} needed)")
        elif 0.2 <= ratio <= 5.0:
            score += 6
            reasons.append(f"Partial/batch quantity fit ({listing.quantity:g} {listing.unit} available)")

    # Clamp score to 100
    final_score = min(100, max(15, score))

    if not reasons:
        reasons.append(f"Circular economy resource in {listing.category.capitalize()}")

    return final_score, reasons
