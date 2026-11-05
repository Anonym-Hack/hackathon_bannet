from app.models import MaterialListing, BuyerRequest
from app.matching_service import compute_match_score

def test_high_compatibility_match():
    listing = MaterialListing(
        title="Post-Industrial HDPE Flake",
        description="Clean high-density polyethylene regrind from bottles",
        category="plastic",
        quantity=10000,
        unit="kg",
        location="Detroit, MI",
        ai_target_industries_json='["Plastics Compounding", "Pipe Extrusion"]',
        ai_reuse_applications_json='["Corrugated pipe manufacturing"]'
    )
    request = BuyerRequest(
        material_name="HDPE Regrind for Pipe Extrusion",
        category="plastic",
        quantity_needed=8000,
        unit="kg",
        location="Detroit, MI",
        use_case="Extruding heavy duty stormwater pipes"
    )
    score, reasons = compute_match_score(listing, request)
    assert score >= 70
    assert len(reasons) >= 2
    assert any("category" in r.lower() for r in reasons)

def test_matches_endpoint_for_listing(client):
    response = client.get("/api/matches/for-listing/2")  # listing 2 is HDPE
    assert response.status_code == 200
    matches = response.json()
    assert isinstance(matches, list)
    if matches:
        assert "match_score" in matches[0]
        assert "why_matched" in matches[0]
