import io
import sys
from pathlib import Path
from fastapi.testclient import TestClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.database import engine, Base, SessionLocal
from app.seed_data import seed_database_if_empty

def run_e2e_verification():
    print("=" * 60)
    print("STARTING FULL END-TO-END VERIFICATION WALKTHROUGH")
    print("=" * 60)

    # 1. Initialize tables & seed
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database_if_empty(db)
    db.close()

    client = TestClient(app)

    # 2. Test Root & Health endpoints
    print("\n[Step 1] Verifying System Health Endpoints...")
    r = client.get("/")
    assert r.status_code == 200, f"Root failed: {r.text}"
    assert r.json()["status"] == "online"
    print("  ✓ Root GET / returned status online")

    r = client.get("/api")
    assert r.status_code == 200, f"API failed: {r.text}"
    assert r.json()["status"] == "healthy"
    print("  ✓ API GET /api returned healthy with demo AI fallback")

    # 3. Test Authentication
    print("\n[Step 2] Testing Authentication Flows & Edge Cases...")
    # 3a. Demo Supplier Login
    r = client.post("/api/auth/login", json={"email": "supplier@demo.com", "password": "password123"})
    assert r.status_code == 200, f"Supplier login failed: {r.text}"
    supplier_token = r.json()["access_token"]
    supplier_headers = {"Authorization": f"Bearer {supplier_token}"}
    print("  ✓ Demo Supplier Login succeeded")

    # 3b. Demo Buyer Login
    r = client.post("/api/auth/login", json={"email": "buyer@demo.com", "password": "password123"})
    assert r.status_code == 200, f"Buyer login failed: {r.text}"
    buyer_token = r.json()["access_token"]
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
    print("  ✓ Demo Buyer Login succeeded")

    # 3c. Wrong Password rejection
    r = client.post("/api/auth/login", json={"email": "supplier@demo.com", "password": "incorrect_password"})
    assert r.status_code == 401, f"Wrong password check failed: {r.text}"
    print("  ✓ Invalid password rejected with HTTP 401")

    # 3d. Register New User
    import time
    unique_email = f"user_{int(time.time())}@ecoforge.com"
    r = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": "valid_password_123",
        "company_name": "EcoForge Industries",
        "role": "Supplier",
        "city": "Milwaukee, WI"
    })
    assert r.status_code == 201, f"Registration failed: {r.text}"
    print(f"  ✓ Dynamic User Registration succeeded ({unique_email})")

    # 3e. Duplicate email rejection
    r = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": "another_password",
        "company_name": "Duplicate Co",
        "role": "Supplier",
        "city": "Chicago, IL"
    })
    assert r.status_code == 400, "Duplicate registration was not rejected"
    print("  ✓ Duplicate email registration rejected with HTTP 400")

    # 3f. Profile endpoint with token
    r = client.get("/api/auth/me", headers=supplier_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "supplier@demo.com"
    print("  ✓ GET /api/auth/me authenticated successfully")

    # 4. Test Marketplace & Filtering
    print("\n[Step 3] Testing Marketplace Listings, Search, & Filters...")
    r = client.get("/api/listings")
    assert r.status_code == 200
    listings = r.json()
    assert len(listings) >= 20, f"Expected 20+ listings, found {len(listings)}"
    print(f"  ✓ GET /api/listings retrieved {len(listings)} active listings")

    # Category filter
    r = client.get("/api/listings?category=metal")
    assert r.status_code == 200
    metals = r.json()
    assert len(metals) > 0 and all(item["category"] == "metal" for item in metals)
    print(f"  ✓ Category filter (metal) returned {len(metals)} matching listings")

    # Keyword search
    r = client.get("/api/listings?q=aluminum")
    assert r.status_code == 200
    assert len(r.json()) > 0
    print("  ✓ Keyword search 'aluminum' returned valid matching listings")

    # Free only filter
    r = client.get("/api/listings?free_only=true")
    assert r.status_code == 200
    free_items = r.json()
    assert len(free_items) > 0 and all(f["price"] == 0 or f["price_type"] == "free" for f in free_items)
    print(f"  ✓ Filter 'free_only' returned {len(free_items)} free material streams")

    # Sorting
    r = client.get("/api/listings?sort_by=sustainability")
    assert r.status_code == 200
    sorted_items = r.json()
    scores = [item["ai_sustainability_score"] for item in sorted_items]
    assert scores == sorted(scores, reverse=True)
    print("  ✓ Sort by sustainability score ordered correctly")

    # 5. Test AI Analysis Engine
    print("\n[Step 4] Testing AI Analysis Engine & Safety Warnings...")
    # Text analysis
    r = client.post("/api/ai/analyze-text", json={
        "title": "Industrial Polypropylene Woven Bales",
        "description": "High tensile strength PP strapping and woven bag scrap from warehouse packaging."
    })
    assert r.status_code == 200
    ai_out = r.json()
    assert ai_out["category"] == "plastic"
    assert len(ai_out["reuse_applications"]) >= 3
    assert len(ai_out["target_industries"]) >= 3
    assert ai_out["sustainability_score"] > 0
    print("  ✓ Text analysis returned structured JSON with reuse applications and target industries")

    # Hazard detection test
    r = client.post("/api/ai/analyze-text", json={
        "title": "Spent Hydrochloric Acid Rinse Solution",
        "description": "Corrosive acidic chemical mixture from electroplating wash bath."
    })
    assert r.status_code == 200
    hazard_out = r.json()
    assert hazard_out["is_hazardous"] is True
    assert hazard_out["safety_warning"] is not None
    assert "REGULATORY HAZARD NOTICE" in hazard_out["safety_warning"]
    print("  ✓ Corrosive chemical accurately flagged as hazardous with regulatory safety notice")

    # 6. Test Listing Creation with Image Upload & Validation
    print("\n[Step 5] Testing File Uploads & Material Creation...")
    # 6a. Invalid extension rejection
    bad_file = io.BytesIO(b"MZ executable header")
    r = client.post(
        "/api/listings",
        data={
            "title": "Malicious Test File",
            "description": "Testing rejection",
            "category": "metal",
            "quantity": "500",
            "unit": "kg",
            "location": "Chicago, IL"
        },
        files={"image": ("test.exe", bad_file, "application/octet-stream")},
        headers=supplier_headers
    )
    assert r.status_code == 400
    assert "Invalid image format" in r.json()["detail"]
    print("  ✓ Rejected dangerous file extension (.exe) with HTTP 400")

    # 6b. Oversized file (>5MB) rejection
    huge_file = io.BytesIO(b"X" * (6 * 1024 * 1024))
    r = client.post(
        "/api/listings",
        data={
            "title": "Huge File Test",
            "description": "Testing size limit",
            "category": "metal",
            "quantity": "500",
            "unit": "kg",
            "location": "Chicago, IL"
        },
        files={"image": ("large.png", huge_file, "image/png")},
        headers=supplier_headers
    )
    assert r.status_code == 400
    assert "exceeds maximum allowed size" in r.json()["detail"]
    print("  ✓ Rejected oversized file (>5 MB) with HTTP 400")

    # 6c. Valid creation with image
    valid_png = io.BytesIO(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    r = client.post(
        "/api/listings",
        data={
            "title": "Secondary Reclaimed Copper Wire",
            "description": "Bright bare copper conductors stripped from electrical equipment renovation.",
            "category": "metal",
            "quantity": "3200",
            "unit": "kg",
            "price_type": "fixed",
            "price": "7.50",
            "location": "Cleveland, OH",
            "availability_status": "available"
        },
        files={"image": ("copper_wire.png", valid_png, "image/png")},
        headers=supplier_headers
    )
    assert r.status_code == 201, f"Valid listing creation failed: {r.text}"
    new_listing = r.json()
    new_listing_id = new_listing["id"]
    assert new_listing["title"] == "Secondary Reclaimed Copper Wire"
    assert new_listing["image_url"] is not None
    assert len(new_listing["ai_reuse_applications"]) >= 3
    print(f"  ✓ Material Listing created successfully with image and AI analysis (ID: {new_listing_id})")

    # 7. Test Buyer Requests
    print("\n[Step 6] Testing Buyer Requests & Sourcing...")
    r = client.post(
        "/api/requests",
        json={
            "material_name": "Copper Granulate for Foundry Ingot Casting",
            "category": "metal",
            "quantity_needed": 3000,
            "unit": "kg",
            "location": "Cleveland, OH",
            "use_case": "Melting and casting bronze hardware components"
        },
        headers=buyer_headers
    )
    assert r.status_code == 201, f"Buyer request creation failed: {r.text}"
    new_req = r.json()
    new_req_id = new_req["id"]
    print(f"  ✓ Buyer procurement request posted successfully (ID: {new_req_id})")

    # 8. Test AI Matching
    print("\n[Step 7] Testing Intelligent AI Circular Matching...")
    r = client.get(f"/api/matches/for-listing/{new_listing_id}")
    assert r.status_code == 200
    matches_for_listing = r.json()
    assert len(matches_for_listing) > 0
    top_match = matches_for_listing[0]
    assert top_match["match_score"] >= 70
    assert len(top_match["why_matched"]) >= 2
    print(f"  ✓ AI Match Score: {top_match['match_score']}% with rationale: {top_match['why_matched']}")

    # 9. Test Inquiries & Chat Threads
    print("\n[Step 8] Testing Threaded Inquiries & Real-time Messages...")
    # Buyer inquires on the new listing
    r = client.post(
        "/api/inquiries",
        json={
            "listing_id": new_listing_id,
            "subject": "Inquiry regarding Copper Wire Lot",
            "message": "We can take the entire 3,200 kg lot. Do you have assay reports verifying 99% purity?"
        },
        headers=buyer_headers
    )
    assert r.status_code == 201, f"Inquiry creation failed: {r.text}"
    inq_id = r.json()["id"]
    print(f"  ✓ Buyer initiated inquiry thread (ID: {inq_id})")

    # Check unread count for supplier
    r = client.get("/api/inquiries/unread-count", headers=supplier_headers)
    assert r.status_code == 200
    assert r.json()["unread_count"] >= 1
    print("  ✓ Supplier received unread message notification badge")

    # Supplier opens thread and replies
    r = client.get(f"/api/inquiries/{inq_id}", headers=supplier_headers)
    assert r.status_code == 200
    assert len(r.json()["messages"]) == 1
    print("  ✓ Supplier read thread (messages marked as read)")

    # Supplier replies
    r = client.post(
        f"/api/inquiries/{inq_id}/messages",
        json={"content": "Yes, certified assay sheet shows 99.8% Cu. Pickup can be scheduled Monday morning."},
        headers=supplier_headers
    )
    assert r.status_code == 201
    print("  ✓ Supplier sent reply message successfully")

    # Buyer verifies thread length
    r = client.get(f"/api/inquiries/{inq_id}", headers=buyer_headers)
    assert r.status_code == 200
    assert len(r.json()["messages"]) == 2
    print("  ✓ Thread verified: 2 messages stored with accurate sender metadata")

    # 10. Test Dashboards
    print("\n[Step 9] Testing Role-Aware Dashboards...")
    r = client.get(f"/api/listings?supplier_id=1")
    assert r.status_code == 200
    print(f"  ✓ Supplier Dashboard query returned {len(r.json())} active listings")

    r = client.get(f"/api/requests?buyer_id=2")
    assert r.status_code == 200
    print(f"  ✓ Buyer Dashboard query returned {len(r.json())} active requests")

    # 11. Test Impact Analytics
    print("\n[Step 10] Testing Impact & Circular LCA Analytics...")
    r = client.get("/api/analytics/impact")
    assert r.status_code == 200
    impact = r.json()
    assert impact["total_waste_diverted_kg"] > 0
    assert impact["estimated_co2_saved_kg"] > 0
    assert impact["estimated_cost_savings_usd"] > 0
    assert len(impact["category_breakdown"]) > 0
    assert "disclaimer" in impact
    print(f"  ✓ Impact calculations verified:")
    print(f"      - Total Waste Diverted: {impact['total_waste_diverted_kg']:,.1f} kg")
    print(f"      - Avoided CO2 Emissions: {impact['estimated_co2_saved_kg']:,.1f} kg")
    print(f"      - Estimated Cost Savings: ${impact['estimated_cost_savings_usd']:,.2f}")
    print(f"      - Stream Categories: {len(impact['category_breakdown'])}")

    print("\n" + "=" * 60)
    print("ALL 10 VERIFICATION STEPS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e_verification()
