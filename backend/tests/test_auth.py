import pytest


async def _register(client, email="reader@example.com", password="password123", name="독자"):
    return await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": name},
    )


async def test_register_returns_token_pair(client):
    res = await _register(client)
    assert res.status_code == 201
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_register_duplicate_email_conflicts(client):
    await _register(client)
    res = await _register(client)
    assert res.status_code == 409


async def test_login_success(client):
    await _register(client)
    res = await client.post(
        "/api/auth/login", json={"email": "reader@example.com", "password": "password123"}
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_login_wrong_password(client):
    await _register(client)
    res = await client.post(
        "/api/auth/login", json={"email": "reader@example.com", "password": "wrong-password"}
    )
    assert res.status_code == 401


async def test_me_requires_valid_token(client):
    res = await client.get("/api/auth/me")
    assert res.status_code == 401

    reg = await _register(client)
    access_token = reg.json()["access_token"]
    res = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert res.status_code == 200
    assert res.json()["email"] == "reader@example.com"


async def test_refresh_rotates_and_invalidates_old_token(client):
    reg = await _register(client)
    old_refresh = reg.json()["refresh_token"]

    res = await client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert res.status_code == 200
    new_refresh = res.json()["refresh_token"]
    assert new_refresh != old_refresh

    # reusing the old (rotated-out) refresh token must fail
    res2 = await client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert res2.status_code == 401

    # the new refresh token should still work
    res3 = await client.post("/api/auth/refresh", json={"refresh_token": new_refresh})
    assert res3.status_code == 200


async def test_logout_revokes_refresh_token(client):
    reg = await _register(client)
    refresh_token = reg.json()["refresh_token"]

    res = await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert res.status_code == 204

    res2 = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert res2.status_code == 401
