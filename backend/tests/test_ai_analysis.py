from app.ai_service import rule_based_analyze, repair_and_validate_ai_json

def test_rule_based_analysis_keyword_matching():
    analysis = rule_based_analyze(
        title="Industrial Brass Turnings & Swarf",
        description="Clean unmixed brass C360 scrap turnings from screw machine production line.",
        category_hint=None
    )
    assert analysis.category == "metal"
    assert len(analysis.reuse_applications) >= 3
    assert len(analysis.target_industries) >= 3
    assert 0 <= analysis.sustainability_score <= 100
    assert analysis.is_demo_mode is True

def test_hazard_detection_and_warning():
    analysis = rule_based_analyze(
        title="Spent Phosphoric Acid Rinse Effluent",
        description="Corrosive acidic chemical mixture from anodizing line wash stage.",
        category_hint=None
    )
    assert analysis.category == "chemical"
    assert analysis.is_hazardous is True
    assert analysis.safety_warning is not None
    assert "REGULATORY HAZARD NOTICE" in analysis.safety_warning

def test_repair_malformed_ai_json():
    # Simulate partial or corrupted response from external LLM
    broken_data = {
        "material_name": "Mixed Wood Shavings",
        "category": "not_a_real_category",  # invalid category
        "sustainability_score": 150,  # out of bounds
        "reuse_applications": None,  # invalid type
        "target_industries": []  # empty
    }
    repaired = repair_and_validate_ai_json(
        broken_data,
        fallback_title="Mixed Wood Shavings",
        fallback_desc="Clean dry pine sawdust shavings from furniture workshop"
    )
    assert repaired.category == "wood"
    assert 0 <= repaired.sustainability_score <= 100
    assert len(repaired.reuse_applications) >= 2
    assert len(repaired.target_industries) >= 2
    assert repaired.material_name == "Mixed Wood Shavings"

def test_ai_analyze_endpoint(client):
    response = client.post("/api/ai/analyze-text", json={
        "title": "Baled Polypropylene Strapping",
        "description": "White PP strapping band scrap from logistics warehouse unbundling"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "plastic"
    assert "sustainability_score" in data
    assert "reuse_applications" in data
