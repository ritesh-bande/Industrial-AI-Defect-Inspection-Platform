
import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app, seed_data
from database.postgres import SessionLocal
from models.models import User
from authentication.jwt import get_password_hash

client = TestClient(app)

def setup_module(module):
    seed_data()
    db = SessionLocal()
    try:
        inactive = db.query(User).filter(User.username == "inactive_user").first()
        if not inactive:
            inactive = User(
                username="inactive_user",
                email="inactive@visioninspect.ai",
                hashed_password=get_password_hash("Password123!"),
                role="operator",
                is_active=False
            )
            db.add(inactive)
            db.commit()
    finally:
        db.close()

def test_valid_login():
    response = client.post("/api/auth/login", json={"email": "admin@visioninspect.ai", "password": "Admin@Vision2026!"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@visioninspect.ai"

def test_wrong_password():
    response = client.post("/api/auth/login", json={"email": "admin@visioninspect.ai", "password": "WrongPassword123!"})
    assert response.status_code == 401
    assert "access_token" not in response.json()
    assert "Invalid email or password" in response.json()["detail"]

def test_nonexistent_email():
    response = client.post("/api/auth/login", json={"email": "fake_nonexistent_user@visioninspect.ai", "password": "Password123!"})
    assert response.status_code == 401
    assert "access_token" not in response.json()
    assert "Invalid email or password" in response.json()["detail"]

def test_empty_credentials():
    response = client.post("/api/auth/login", json={"email": "", "password": ""})
    assert response.status_code in [400, 422]

def test_invalid_email_format():
    response = client.post("/api/auth/login", json={"email": "invalid_email_format", "password": "Password123!"})
    assert response.status_code in [400, 422]

def test_inactive_user_login():
    response = client.post("/api/auth/login", json={"email": "inactive@visioninspect.ai", "password": "Password123!"})
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()

def test_protected_me_endpoint_valid_token():
    login_res = client.post("/api/auth/login", json={"email": "admin@visioninspect.ai", "password": "Admin@Vision2026!"})
    token = login_res.json()["access_token"]
    
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@visioninspect.ai"

def test_protected_endpoint_no_token():
    res = client.get("/api/auth/me")
    assert res.status_code == 401

def test_protected_endpoint_invalid_token():
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_fake_token_123"})
    assert res.status_code == 401

def test_forgot_password_generic_response():
    res1 = client.post("/api/auth/forgot-password", json={"email": "riteshbande992@gmail.com"})
    assert res1.status_code == 200
    assert "If an account exists" in res1.json()["message"]

    res2 = client.post("/api/auth/forgot-password", json={"email": "completely_unknown_user@example.com"})
    assert res2.status_code == 200
    assert "If an account exists" in res2.json()["message"]

def test_reset_password_invalid_token():
    res = client.post("/api/auth/reset-password", json={"token": "invalid_raw_token_xyz", "new_password": "NewSecurePassword123!"})
    assert res.status_code == 400
    assert "invalid or has expired" in res.json()["detail"].lower()

def test_end_to_end_password_reset_flow():
    email = "admin@visioninspect.ai"
    old_pass = "Admin@Vision2026!"
    new_pass = "NewAdminSecure2026!"

    # 1. Request forgot password
    client.post("/api/auth/forgot-password", json={"email": email})

    # 2. Retrieve token from test DB
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        from models.models import PasswordResetToken
        reset_rec = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at == None).order_by(PasswordResetToken.id.desc()).first()
        assert reset_rec is not None

        # 3. Simulate raw token reset (test token hash logic)
        import hashlib, secrets
        raw_token = secrets.token_urlsafe(32)
        reset_rec.token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        db.commit()
    finally:
        db.close()

    # 4. Perform password reset
    reset_res = client.post("/api/auth/reset-password", json={"token": raw_token, "new_password": new_pass})
    assert reset_res.status_code == 200

    # 5. Verify old password fails
    fail_res = client.post("/api/auth/login", json={"email": email, "password": old_pass})
    assert fail_res.status_code == 401

    # 6. Verify new password succeeds
    succ_res = client.post("/api/auth/login", json={"email": email, "password": new_pass})
    assert succ_res.status_code == 200
    assert "access_token" in succ_res.json()

