"""
Tests for Authentication, Sessions, Password Recovery, and /me
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success_and_cookie(client: AsyncClient, seeded_test_data):
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@school1.org", "password": "AdminPass123!"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "session_token" in data
    assert data["user"]["email"] == "admin@school1.org"
    assert data["user"]["role"] == "admin"
    assert "mind_session" in res.cookies


@pytest.mark.asyncio
async def test_login_failure_invalid_password(client: AsyncClient, seeded_test_data):
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@school1.org", "password": "WrongPassword!"}
    )
    assert res.status_code == 401
    err = res.json()
    assert err["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_me_with_bearer_token(client: AsyncClient, seeded_test_data):
    # 1. Login to get token
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "teacher1@school1.org", "password": "TeacherPass123!"}
    )
    token = login_res.json()["session_token"]

    # 2. Call /me with Bearer token
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    me_data = res.json()
    assert me_data["user"]["email"] == "teacher1@school1.org"
    assert me_data["user"]["role"] == "teacher"
    assert me_data["school"]["name"] == "Springfield Academy"


@pytest.mark.asyncio
async def test_logout_terminates_session(client: AsyncClient, seeded_test_data):
    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "student1@school1.org", "password": "StudentPass123!"}
    )
    token = login_res.json()["session_token"]

    # 2. Call logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_res.status_code == 200

    # 3. Call /me with invalidated session token - should be 401
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(client: AsyncClient, seeded_test_data):
    # 1. Request password reset
    forgot_res = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "admin@school1.org"}
    )
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json().get("reset_token_dev")
    assert reset_token is not None

    # 2. Complete reset with new password
    reset_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "NewAdminPass456!"}
    )
    assert reset_res.status_code == 200

    # 3. Old password should fail
    old_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@school1.org", "password": "AdminPass123!"}
    )
    assert old_res.status_code == 401

    # 4. New password should succeed
    new_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@school1.org", "password": "NewAdminPass456!"}
    )
    assert new_res.status_code == 200
