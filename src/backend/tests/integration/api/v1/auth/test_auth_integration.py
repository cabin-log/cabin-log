import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import app.core.db.session as database
from app.models.user import User
from tests.fixtures.payload_data import (
    INVALID_EMAIL,
    VALID_PASSWORD,
    build_login_payload,
    build_signup_payload,
)
from tests.fixtures.scenario_seed_data import (
    SEEDED_PRIMARY_EMAIL,
    SEEDED_PRIMARY_NAME,
    SEEDED_PRIMARY_PASSWORD,
)


async def _set_user_role_by_email(email: str, role: str) -> None:
    session_factory = database.get_session_factory()
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise AssertionError(f"Expected user for role update was not found: {email}")
        user.role = role
        await session.commit()


@pytest.mark.primary_data
def test_signup_and_login_flow(integration_client: TestClient):
    """Scenario: a new user can signup and login through real service+DB flow."""
    # Given: clean integration database from fixture.
    # When: user signs up with a valid payload.
    signup_response = integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="integration-user@example.com",
            name="Integration User",
            password=VALID_PASSWORD,
        ),
    )
    # Then: signup succeeds with user payload.
    assert signup_response.status_code == 200
    assert signup_response.json()["email"] == "integration-user@example.com"

    # When: same user logs in with valid credentials.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="integration-user@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )
    # Then: token contract is returned.
    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "integration-user@example.com"
    assert payload["access_token"]


@pytest.mark.primary_data
def test_me_with_bearer_token(integration_client: TestClient):
    """Scenario: /me returns current user when bearer token is valid."""
    # Given: a signed-up user.
    integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="me-user@example.com",
            name="Me User",
            password=VALID_PASSWORD,
        ),
    )
    # When: user logs in and gets an access token.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="me-user@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )
    access_token = login_response.json()["access_token"]

    # And: token is used on protected /me.
    me_response = integration_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # Then: user profile is returned.
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "me-user@example.com"


@pytest.mark.primary_data
def test_signup_duplicate_email_returns_409(integration_client: TestClient):
    """Scenario: signup returns domain conflict error for duplicate email."""
    payload = build_signup_payload(
        email="duplicate-user@example.com",
        name="Duplicate User",
        password=VALID_PASSWORD,
    )

    # Given: first signup is successful.
    first_response = integration_client.post("/api/v1/auth/signup", json=payload)
    assert first_response.status_code == 200

    # When: same email signs up again.
    second_response = integration_client.post("/api/v1/auth/signup", json=payload)
    # Then: auth domain error is returned.
    assert second_response.status_code == 409
    assert second_response.json()["detail"]["error"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.primary_data
def test_password_auth_disabled_blocks_email_password_entrypoints(
    password_auth_disabled_integration_client: TestClient,
):
    """Scenario: Cabinlog can keep login on while disabling legacy password auth routes."""
    signup_response = password_auth_disabled_integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="disabled-signup@example.com",
            name="Disabled Signup",
            password=VALID_PASSWORD,
        ),
    )
    assert signup_response.status_code == 403
    assert signup_response.json()["detail"]["error"] == "PASSWORD_AUTH_DISABLED"

    login_response = password_auth_disabled_integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="disabled-signup@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )
    assert login_response.status_code == 403
    assert login_response.json()["detail"]["error"] == "PASSWORD_AUTH_DISABLED"

    token_response = password_auth_disabled_integration_client.post(
        "/api/v1/auth/token",
        data={
            "username": "disabled-signup@example.com",
            "password": VALID_PASSWORD,
        },
    )
    assert token_response.status_code == 403
    assert token_response.json()["detail"]["error"] == "PASSWORD_AUTH_DISABLED"

    forgot_password_response = password_auth_disabled_integration_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "disabled-signup@example.com"},
    )
    assert forgot_password_response.status_code == 403
    assert forgot_password_response.json()["detail"]["error"] == "PASSWORD_AUTH_DISABLED"

    config_response = password_auth_disabled_integration_client.get("/config")
    assert config_response.status_code == 200
    assert config_response.json()["login_enabled"] is True
    assert config_response.json()["password_auth_enabled"] is False


@pytest.mark.primary_data
def test_login_invalid_password_returns_401(integration_client: TestClient):
    """Scenario: login returns invalid credentials for wrong password."""
    # Given: existing user in DB.
    integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="wrong-pass@example.com",
            name="Wrong Pass User",
            password=VALID_PASSWORD,
        ),
    )

    # When: login is attempted with wrong password.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="wrong-pass@example.com",
            password="InvalidPass1!",
            remember_me=False,
        ),
    )

    # Then: auth domain error is returned.
    assert login_response.status_code == 401
    assert login_response.json()["detail"]["error"] == "INVALID_CREDENTIALS"


@pytest.mark.primary_data
def test_signup_invalid_email_or_password_returns_422(integration_client: TestClient):
    """Scenario: schema-level validation rejects malformed signup payloads."""
    # Given/When: malformed email is submitted.
    invalid_email_response = integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email=INVALID_EMAIL,
            name="Invalid Email",
            password=VALID_PASSWORD,
        ),
    )
    # Then: validation error is returned.
    assert invalid_email_response.status_code == 422

    # Given/When: password policy-violating payload is submitted.
    invalid_password_response = integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="invalid-password@example.com",
            name="Invalid Password",
            password="alllowercase1!",
        ),
    )
    # Then: validation error is returned.
    assert invalid_password_response.status_code == 422


@pytest.mark.primary_data
def test_admin_stats_forbidden_for_non_admin(integration_client: TestClient):
    """Scenario: admin-only stats endpoint rejects authenticated non-admin users."""
    # Given: regular user is created and logged in.
    integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="rbac-user@example.com",
            name="RBAC User",
            password=VALID_PASSWORD,
        ),
    )
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="rbac-user@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )
    access_token = login_response.json()["access_token"]

    # When: non-admin user requests admin stats.
    admin_stats_response = integration_client.get(
        "/api/v1/auth/admin/user-role-stats",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Then: permission error is returned.
    assert admin_stats_response.status_code == 403
    assert admin_stats_response.json()["detail"]["error"] == "INSUFFICIENT_ROLE"


@pytest.mark.primary_data
def test_admin_stats_success_for_admin(integration_client: TestClient):
    """Scenario: promoted admin user can access admin role stats endpoint."""
    # Given: user is created then promoted to admin role at DB layer.
    integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="rbac-admin@example.com",
            name="RBAC Admin",
            password=VALID_PASSWORD,
        ),
    )
    asyncio.run(_set_user_role_by_email("rbac-admin@example.com", "admin"))

    login_response = integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="rbac-admin@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )
    access_token = login_response.json()["access_token"]

    # When: admin user requests role stats.
    admin_stats_response = integration_client.get(
        "/api/v1/auth/admin/user-role-stats",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Then: stats payload is returned with at least one admin account.
    assert admin_stats_response.status_code == 200
    stats_payload = admin_stats_response.json()
    assert stats_payload["total_users"] >= 1
    assert stats_payload["admin_users"] >= 1


@pytest.mark.mocked_data
def test_seeded_primary_user_can_login(seeded_integration_client: TestClient):
    """Scenario: seeded baseline user can login in production-like preloaded dataset."""
    # Given: integration fixture preloaded with baseline user + existing users.
    # When: login is attempted with seeded baseline credentials.
    login_response = seeded_integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email=SEEDED_PRIMARY_EMAIL,
            password=SEEDED_PRIMARY_PASSWORD,
            remember_me=False,
        ),
    )

    # Then: authentication succeeds and token contract is returned.
    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == SEEDED_PRIMARY_EMAIL
    assert login_response.json()["user"]["role"] == "admin"


@pytest.mark.mocked_data
def test_seeded_dataset_duplicate_email_signup_returns_409(
    seeded_integration_client: TestClient,
):
    """Scenario: signup detects duplicate email against preloaded user dataset."""
    # Given: seeded baseline user already exists in DB.
    # When: signup is attempted with the same baseline email.
    duplicate_response = seeded_integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email=SEEDED_PRIMARY_EMAIL,
            name=SEEDED_PRIMARY_NAME,
            password=SEEDED_PRIMARY_PASSWORD,
        ),
    )

    # Then: domain conflict error is returned.
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"]["error"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.primary_data
@pytest.mark.email_enabled
def test_email_enabled_signup_requires_verification_before_login(
    email_enabled_integration_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Scenario: when EMAIL_ENABLED=true, login is blocked until email verification is completed."""
    fixed_verification_token = "integration-email-verify-token"
    monkeypatch.setattr(
        "app.services.auth.create_email_verification_token",
        lambda: fixed_verification_token,
    )

    # Given: signup succeeds while email verification is required.
    signup_response = email_enabled_integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="verify-required@example.com",
            name="Verify Required",
            password=VALID_PASSWORD,
        ),
        headers={"X-App-Language": "ko"},
    )
    assert signup_response.status_code == 200

    # When: user attempts login before verification.
    blocked_login_response = email_enabled_integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="verify-required@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )

    # Then: login is rejected with EMAIL_NOT_VERIFIED.
    assert blocked_login_response.status_code == 403
    assert blocked_login_response.json()["detail"]["error"] == "EMAIL_NOT_VERIFIED"

    # When: verification token is consumed via verify-email endpoint.
    verify_response = email_enabled_integration_client.post(
        "/api/v1/auth/verify-email",
        json={"token": fixed_verification_token},
    )
    assert verify_response.status_code == 200

    # Then: login succeeds after verification.
    login_after_verify_response = email_enabled_integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="verify-required@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )
    assert login_after_verify_response.status_code == 200
    assert login_after_verify_response.json()["user"]["email"] == "verify-required@example.com"


@pytest.mark.primary_data
@pytest.mark.email_enabled
def test_email_enabled_forgot_password_issues_reset_token(
    email_enabled_integration_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Scenario: when EMAIL_ENABLED=true, forgot-password returns success and issues reset token."""
    fixed_password_reset_token = "integration-password-reset-token"
    monkeypatch.setattr(
        "app.services.auth.create_password_reset_token",
        lambda: fixed_password_reset_token,
    )

    # Given: a signed-up user in email-enabled mode.
    signup_response = email_enabled_integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="reset-enabled@example.com",
            name="Reset Enabled",
            password=VALID_PASSWORD,
        ),
        headers={"X-App-Language": "en"},
    )
    assert signup_response.status_code == 200

    # When: forgot-password endpoint is requested.
    forgot_password_response = email_enabled_integration_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset-enabled@example.com"},
        headers={"X-App-Language": "ko"},
    )

    # Then: endpoint returns accepted contract and issued token can be consumed.
    assert forgot_password_response.status_code == 200
    reset_password_response = email_enabled_integration_client.post(
        "/api/v1/auth/reset-password",
        json={"token": fixed_password_reset_token, "password": "NewValidPass1!"},
    )
    assert reset_password_response.status_code == 200

    # And: user can login with rotated password (still blocked until verify-email).
    login_after_reset_response = email_enabled_integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="reset-enabled@example.com",
            password="NewValidPass1!",
            remember_me=False,
        ),
    )
    assert login_after_reset_response.status_code == 403
    assert login_after_reset_response.json()["detail"]["error"] == "EMAIL_NOT_VERIFIED"
