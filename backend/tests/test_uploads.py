import io

def test_invalid_file_extension(client, supplier_token):
    headers = {"Authorization": f"Bearer {supplier_token}"}
    fake_exe = io.BytesIO(b"MZ executable content")
    files = {"image": ("malware.exe", fake_exe, "application/octet-stream")}
    data = {
        "title": "Listing with bad file",
        "description": "Testing extension check",
        "category": "metal",
        "quantity": 100,
        "unit": "kg",
        "price_type": "fixed",
        "price": 10,
        "location": "Chicago, IL"
    }
    response = client.post("/api/listings", data=data, files=files, headers=headers)
    assert response.status_code == 400
    assert "Invalid image format" in response.json()["detail"]

def test_file_size_limit(client, supplier_token):
    headers = {"Authorization": f"Bearer {supplier_token}"}
    # 6MB dummy image file
    huge_bytes = io.BytesIO(b"0" * (6 * 1024 * 1024))
    files = {"image": ("large.png", huge_bytes, "image/png")}
    data = {
        "title": "Listing with huge file",
        "description": "Testing size limit check",
        "category": "metal",
        "quantity": 100,
        "unit": "kg",
        "price_type": "fixed",
        "price": 10,
        "location": "Chicago, IL"
    }
    response = client.post("/api/listings", data=data, files=files, headers=headers)
    assert response.status_code == 400
    assert "exceeds maximum allowed size" in response.json()["detail"]
