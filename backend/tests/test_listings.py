def test_get_listings_list(client):
    response = client.get("/api/listings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 20

def test_filter_listings_by_category(client):
    response = client.get("/api/listings?category=plastic")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for item in data:
        assert item["category"] == "plastic"

def test_search_listings(client):
    response = client.get("/api/listings?q=aluminum")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any("aluminum" in item["title"].lower() for item in data)

def test_create_listing_as_supplier(client, supplier_token):
    headers = {"Authorization": f"Bearer {supplier_token}"}
    payload = {
        "title": "Recycled PET Clear Flake",
        "description": "Hot-washed post-consumer PET bottle flake. Clear transparent grade, PVC contamination under 20 ppm.",
        "category": "plastic",
        "quantity": 5000,
        "unit": "kg",
        "price_type": "fixed",
        "price": 1.10,
        "location": "Indianapolis, IN",
        "availability_status": "available"
    }
    response = client.post("/api/listings", data=payload, headers=headers)
    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Recycled PET Clear Flake"
    assert created["category"] == "plastic"
    assert "ai_reuse_applications" in created
    assert len(created["ai_reuse_applications"]) >= 2

def test_buyer_forbidden_from_creating_listing(client, buyer_token):
    headers = {"Authorization": f"Bearer {buyer_token}"}
    payload = {
        "title": "Unauthorized Listing",
        "description": "Trying to post as buyer",
        "category": "metal",
        "quantity": 100,
        "unit": "kg",
        "price_type": "free",
        "price": 0,
        "location": "Detroit, MI"
    }
    response = client.post("/api/listings", data=payload, headers=headers)
    assert response.status_code == 403
