def test_create_and_reply_inquiry(client, buyer_token, supplier_token):
    # 1. Buyer sends inquiry on listing 1 (owned by supplier)
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
    supplier_headers = {"Authorization": f"Bearer {supplier_token}"}

    inq_payload = {
        "listing_id": 1,
        "subject": "Bulk purchase inquiry for Aluminum",
        "message": "Can you provide a certificate of analysis for this aluminum lot?"
    }
    create_res = client.post("/api/inquiries", json=inq_payload, headers=buyer_headers)
    assert create_res.status_code == 201
    inquiry_data = create_res.json()
    inquiry_id = inquiry_data["id"]
    assert inquiry_data["subject"] == inq_payload["subject"]

    # 2. Supplier replies
    reply_payload = {
        "content": "Yes, COA is attached and we can ship within 48 hours."
    }
    reply_res = client.post(f"/api/inquiries/{inquiry_id}/messages", json=reply_payload, headers=supplier_headers)
    assert reply_res.status_code == 201
    assert reply_res.json()["content"] == reply_payload["content"]

    # 3. Check thread view
    thread_res = client.get(f"/api/inquiries/{inquiry_id}", headers=buyer_headers)
    assert thread_res.status_code == 200
    thread = thread_res.json()
    assert len(thread["messages"]) == 2

def test_cannot_inquire_on_own_listing(client, supplier_token):
    # Supplier owns listing 1
    supplier_headers = {"Authorization": f"Bearer {supplier_token}"}
    inq_payload = {
        "listing_id": 1,
        "subject": "Self inquiry",
        "message": "Testing self message"
    }
    res = client.post("/api/inquiries", json=inq_payload, headers=supplier_headers)
    assert res.status_code == 400
