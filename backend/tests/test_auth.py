from datetime import datetime, timedelta, timezone


async def _verify_and_register(
    client, sent_verification_codes, email="reader@example.com", password="password123", name="독자"
):
    await client.post("/api/auth/send-verification-code", json={"email": email})
    code = sent_verification_codes[-1][1]
    await client.post("/api/auth/confirm-verification-code", json={"email": email, "code": code})
    return await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": name},
    )


async def test_register_returns_token_pair(client, sent_verification_codes):
    res = await _verify_and_register(client, sent_verification_codes)
    assert res.status_code == 201
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_register_without_verification_is_rejected(client):
    res = await client.post(
        "/api/auth/register",
        json={"email": "reader@example.com", "password": "password123", "name": "독자"},
    )
    assert res.status_code == 400


async def test_register_with_expired_code_verification_is_rejected(client, db, sent_verification_codes):
    email = "reader@example.com"
    await client.post("/api/auth/send-verification-code", json={"email": email})
    code = sent_verification_codes[-1][1]
    await client.post("/api/auth/confirm-verification-code", json={"email": email, "code": code})

    # simulate the completion window having elapsed since confirmation
    await db.email_verification_codes.update_one(
        {"email": email},
        {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}},
    )

    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "name": "독자"},
    )
    assert res.status_code == 400


async def test_register_duplicate_email_conflicts(client, sent_verification_codes):
    await _verify_and_register(client, sent_verification_codes)
    res = await _verify_and_register(client, sent_verification_codes)
    assert res.status_code == 409


async def test_login_success(client, sent_verification_codes):
    await _verify_and_register(client, sent_verification_codes)
    res = await client.post(
        "/api/auth/login", json={"email": "reader@example.com", "password": "password123"}
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_login_wrong_password(client, sent_verification_codes):
    await _verify_and_register(client, sent_verification_codes)
    res = await client.post(
        "/api/auth/login", json={"email": "reader@example.com", "password": "wrong-password"}
    )
    assert res.status_code == 401


async def test_me_requires_valid_token(client, sent_verification_codes):
    res = await client.get("/api/auth/me")
    assert res.status_code == 401

    reg = await _verify_and_register(client, sent_verification_codes)
    access_token = reg.json()["access_token"]
    res = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert res.status_code == 200
    assert res.json()["email"] == "reader@example.com"
    assert res.json()["email_verified"] is True


async def test_refresh_rotates_and_invalidates_old_token(client, sent_verification_codes):
    reg = await _verify_and_register(client, sent_verification_codes)
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


async def test_logout_revokes_refresh_token(client, sent_verification_codes):
    reg = await _verify_and_register(client, sent_verification_codes)
    refresh_token = reg.json()["refresh_token"]

    res = await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert res.status_code == 204

    res2 = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert res2.status_code == 401


async def test_check_email_available(client):
    res = await client.get("/api/auth/check-email", params={"email": "new@example.com"})
    assert res.status_code == 200
    assert res.json() == {"available": True}


async def test_check_email_taken(client, sent_verification_codes):
    await _verify_and_register(client, sent_verification_codes)
    res = await client.get("/api/auth/check-email", params={"email": "reader@example.com"})
    assert res.status_code == 200
    assert res.json() == {"available": False}


async def test_send_verification_code_rejects_already_registered_email(
    client, sent_verification_codes
):
    await _verify_and_register(client, sent_verification_codes)
    res = await client.post(
        "/api/auth/send-verification-code", json={"email": "reader@example.com"}
    )
    assert res.status_code == 409


async def test_confirm_verification_code_requires_a_sent_code(client):
    res = await client.post(
        "/api/auth/confirm-verification-code",
        json={"email": "reader@example.com", "code": "123456"},
    )
    assert res.status_code == 400


async def test_confirm_verification_code_rejects_wrong_code(client, sent_verification_codes):
    email = "reader@example.com"
    await client.post("/api/auth/send-verification-code", json={"email": email})
    real_code = sent_verification_codes[-1][1]
    wrong_code = "000000" if real_code != "000000" else "111111"

    res = await client.post(
        "/api/auth/confirm-verification-code", json={"email": email, "code": wrong_code}
    )
    assert res.status_code == 400

    # the correct code still works afterwards (attempt wasn't locked out yet)
    res2 = await client.post(
        "/api/auth/confirm-verification-code", json={"email": email, "code": real_code}
    )
    assert res2.status_code == 204


async def test_confirm_verification_code_locks_out_after_max_attempts(client, sent_verification_codes):
    email = "reader@example.com"
    await client.post("/api/auth/send-verification-code", json={"email": email})
    real_code = sent_verification_codes[-1][1]
    wrong_code = "000000" if real_code != "000000" else "111111"

    for _ in range(5):
        res = await client.post(
            "/api/auth/confirm-verification-code", json={"email": email, "code": wrong_code}
        )
        assert res.status_code == 400

    # even the correct code is now rejected until a new one is requested
    res = await client.post(
        "/api/auth/confirm-verification-code", json={"email": email, "code": real_code}
    )
    assert res.status_code == 400


async def test_resending_verification_code_invalidates_the_old_one(client, sent_verification_codes):
    email = "reader@example.com"
    await client.post("/api/auth/send-verification-code", json={"email": email})
    first_code = sent_verification_codes[-1][1]

    await client.post("/api/auth/send-verification-code", json={"email": email})
    second_code = sent_verification_codes[-1][1]

    res = await client.post(
        "/api/auth/confirm-verification-code", json={"email": email, "code": second_code}
    )
    assert res.status_code == 204

    if first_code != second_code:
        res2 = await client.post(
            "/api/auth/confirm-verification-code", json={"email": email, "code": first_code}
        )
        assert res2.status_code == 400
