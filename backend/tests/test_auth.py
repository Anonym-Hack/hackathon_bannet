def test_demo_login_success(client):
    response = client.post("/api/auth/login", json={
        "email": "supplier@demo.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "supplier@demo.com"
    assert data["user"]["role"] == "Supplier"

def test_login_invalid_password(client):
    response = client.post("/api/auth/login", json={
        "email": "supplier@demo.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_register_new_user(client):
    response = client.post("/api/auth/register", json={
        "email": "newbuyer@acme.com",
        "password": "securepassword123",
        "company_name": "Acme Polymers",
        "role": "Buyer",
        "city": "Cleveland, OH"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "newbuyer@acme.com"
    assert data["user"]["company_name"] == "Acme Polymers"

def test_register_duplicate_email(client):
    response = client.post("/api/auth/register", json={
        "email": "supplier@demo.com",
        "password": "anotherpassword",
        "company_name": "Duplicate Inc",
        "role": "Supplier",
        "city": "Chicago, IL"
    })
    assert response.status_code == 400

def test_get_current_user_profile(client, supplier_token):
    headers = {"Authorization": f"Bearer {supplier_token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "supplier@demo.com"
