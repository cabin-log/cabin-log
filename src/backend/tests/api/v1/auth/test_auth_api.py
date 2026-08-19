from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config.settings import SETTINGS
from app.deps import get_current_admin_user, get_current_user
from app.main import register_exception_handlers
from app.models.github import GitHubProfileResponse, GitHubProfiles
from app.models.oauth import OAuthProvider, OAuthProviderPublicConfig
from app.models.user import (
    LoginForm,
    LoginResponse,
    RefreshResponse,
    SignupForm,
    UserResponse,
    UserRoleStatsResponse,
)
from app.routers.v1 import auth
from app.services.auth import AuthService
from tests.fixtures.api_contract_data import (
    AUTH_PASSWORD_POLICY_CASES,
    AUTH_REFRESH_REQUEST_PAYLOAD,
)
from tests.fixtures.payload_data import (
    INVALID_EMAIL,
    VALID_PASSWORD,
    build_login_payload,
    build_signup_payload,
)

pytestmark = pytest.mark.api_test


class FakeAuthService:
    last_preferred_language: str | None = None

    def __init__(self, user: UserResponse):
        self._user = user

    async def signup(
        self, _form: SignupForm, preferred_language: str | None = None
    ) -> UserResponse:
        FakeAuthService.last_preferred_language = preferred_language
        return self._user

    async def login(
        self,
        form: LoginForm,
        _request,
        refresh_session_id: str,
    ) -> LoginResponse:
        return LoginResponse(
            access_token=f"access-token-for-{self._user.id}",
            refresh_token=f"refresh-token-for-{refresh_session_id}",
            token_type="bearer",
            user=self._user,
        )

    def get_oauth_provider_public_configs(self) -> list[OAuthProviderPublicConfig]:
        return [
            OAuthProviderPublicConfig(
                provider=OAuthProvider.GOOGLE,
                start_path="/api/v1/auth/oauth/google/start",
            )
        ]

    def require_oauth_callback_params(
        self,
        *,
        provider: OAuthProvider,
        code: str | None,
        state: str | None,
    ) -> tuple[str, str]:
        _ = provider
        if not code or not state:
            raise AssertionError("Fake callback requires code and state.")
        return code, state

    async def oauth_callback_login(
        self,
        provider: OAuthProvider,
        code: str,
        state: str,
        redirect_uri: str,
        request,
        refresh_session_id: str,
    ) -> LoginResponse:
        _ = provider
        _ = code
        _ = state
        _ = redirect_uri
        _ = request
        return LoginResponse(
            access_token=f"oauth-access-token-for-{self._user.id}",
            refresh_token=f"oauth-refresh-token-for-{refresh_session_id}",
            token_type="bearer",
            user=self._user,
        )

    async def refresh_with_request_context(
        self,
        *,
        request,
        refresh_token: str | None,
        user_id: int | None,
        session_id: str | None,
    ) -> tuple[RefreshResponse, str, bool]:
        _ = request
        _ = refresh_token
        _ = user_id
        return (
            RefreshResponse(
                access_token="rotated-access-token",
                refresh_token="rotated-refresh-token",
                token_type="bearer",
            ),
            session_id or "session-mock-001",
            False,
        )

    async def logout(self, user_id: int) -> None:
        _ = user_id
        return None

    async def resend_verification_email(
        self,
        email: str,
        preferred_language: str | None = None,
    ) -> None:
        _ = email
        FakeAuthService.last_preferred_language = preferred_language
        return None

    async def request_password_reset(
        self,
        email: str,
        preferred_language: str | None = None,
    ) -> None:
        _ = email
        FakeAuthService.last_preferred_language = preferred_language
        return None

    async def get_admin_user_role_stats(self) -> UserRoleStatsResponse:
        return UserRoleStatsResponse(total_users=51, active_users=51, admin_users=1)


def create_auth_test_client(user: UserResponse, with_user_auth: bool = False) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.dependency_overrides[AuthService] = lambda: FakeAuthService(user)
    if with_user_auth:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def create_auth_admin_test_client(admin_user: UserResponse) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.dependency_overrides[AuthService] = lambda: FakeAuthService(admin_user)
    app.dependency_overrides[get_current_admin_user] = lambda: admin_user
    return TestClient(app)


def test_signup_success(sample_user: UserResponse):
    """Scenario: signup route returns user payload on valid input."""
    client = create_auth_test_client(sample_user)

    # Given/When: valid signup payload is submitted.
    response = client.post("/api/v1/auth/signup", json=build_signup_payload())

    # Then: route returns success contract.
    assert response.status_code == 200
    assert response.json()["email"] == "tester@example.com"


def test_signup_prefers_x_app_language_header(sample_user: UserResponse):
    """Scenario: signup passes X-App-Language header to service when both language headers exist."""
    FakeAuthService.last_preferred_language = None
    client = create_auth_test_client(sample_user)
    response = client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(),
        headers={
            "X-App-Language": "ko",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    assert response.status_code == 200
    assert FakeAuthService.last_preferred_language == "ko"


def test_signup_validation_error_returns_422(sample_user: UserResponse):
    """Scenario: signup rejects password that violates schema constraints."""
    client = create_auth_test_client(sample_user)

    # Given/When: weak password is submitted.
    response = client.post("/api/v1/auth/signup", json=build_signup_payload(password="weakpass"))

    # Then: request validation fails before service logic.
    assert response.status_code == 422


def test_signup_invalid_email_format_returns_422(sample_user: UserResponse):
    """Scenario: signup rejects invalid email format."""
    client = create_auth_test_client(sample_user)

    # Given/When: malformed email is submitted.
    response = client.post("/api/v1/auth/signup", json=build_signup_payload(email=INVALID_EMAIL))

    # Then: request validation fails.
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("password", "expected_fragment"),
    AUTH_PASSWORD_POLICY_CASES,
)
def test_signup_password_policy_validation_returns_422(
    sample_user: UserResponse, password: str, expected_fragment: str
):
    """Scenario: signup enforces password policy branches."""
    client = create_auth_test_client(sample_user)

    # Given/When: policy-violating password is submitted.
    response = client.post("/api/v1/auth/signup", json=build_signup_payload(password=password))

    # Then: request is rejected with validation context.
    assert response.status_code == 422
    assert expected_fragment in str(response.json()).lower()


def test_login_invalid_email_format_returns_422(sample_user: UserResponse):
    """Scenario: login rejects malformed email payload."""
    client = create_auth_test_client(sample_user)

    # Given/When: login is attempted with malformed email.
    response = client.post("/api/v1/auth/login", json=build_login_payload(email=INVALID_EMAIL))

    # Then: request validation fails.
    assert response.status_code == 422


def test_oauth_providers_success(sample_user: UserResponse):
    """Scenario: oauth providers route returns configured provider list."""
    client = create_auth_test_client(sample_user)

    # When: provider list is requested.
    response = client.get("/api/v1/auth/oauth/providers")

    # Then: one provider from fake service is returned.
    assert response.status_code == 200
    assert response.json()["providers"][0]["provider"] == "google"


def test_oauth_callback_json_mode_returns_tokens_and_github_profile(
    sample_user: UserResponse,
    monkeypatch: pytest.MonkeyPatch,
):
    """Scenario: backend-only OAuth callback mode returns token payload for Swagger/manual use."""
    original_mode = SETTINGS.OAUTH_CALLBACK_RESPONSE_MODE
    object.__setattr__(SETTINGS, "OAUTH_CALLBACK_RESPONSE_MODE", "json")

    async def fake_get_profile_by_user_id(user_id: int):
        return GitHubProfileResponse(
            user_id=user_id,
            github_user_id=987654,
            login="octodev",
            display_name="Octo Dev",
            avatar_url="https://avatars.githubusercontent.com/u/987654?v=4",
            profile_url="https://github.com/octodev",
            updated_at=datetime.now(UTC),
        )

    monkeypatch.setattr(GitHubProfiles, "get_profile_by_user_id", fake_get_profile_by_user_id)

    try:
        client = create_auth_test_client(sample_user)
        response = client.get(
            "/api/v1/auth/oauth/github/callback",
            params={"code": "github-code", "state": "state-token"},
        )
    finally:
        object.__setattr__(SETTINGS, "OAUTH_CALLBACK_RESPONSE_MODE", original_mode)

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"] == f"oauth-access-token-for-{sample_user.id}"
    assert payload["refresh_token"]
    assert payload["user"]["id"] == sample_user.id
    assert payload["github_profile"]["login"] == "octodev"


def test_login_success_returns_token_contract(sample_user: UserResponse):
    """Scenario: login route returns token payload on valid input."""
    client = create_auth_test_client(sample_user)

    # Given/When: valid login payload is submitted.
    response = client.post(
        "/api/v1/auth/login",
        json=build_login_payload(email=sample_user.email, password=VALID_PASSWORD),
    )

    # Then: login contract includes bearer tokens and user.
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == sample_user.email
    assert payload["access_token"]
    assert payload["refresh_token"]


def test_refresh_success_returns_rotated_token_contract(sample_user: UserResponse):
    """Scenario: refresh route returns rotated access/refresh token payload."""
    client = create_auth_test_client(sample_user)

    # Given/When: refresh request payload is submitted.
    response = client.post("/api/v1/auth/refresh", json=AUTH_REFRESH_REQUEST_PAYLOAD)

    # Then: refresh contract contains rotated token values.
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"] == "rotated-access-token"
    assert payload["refresh_token"] == "rotated-refresh-token"


def test_me_requires_authentication(sample_user: UserResponse):
    """Scenario: protected route denies access without auth dependency."""
    client = create_auth_test_client(sample_user)

    # When: /me is requested without overriding get_current_user.
    response = client.get("/api/v1/auth/me")

    # Then: auth guard returns invalid token error.
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "INVALID_TOKEN"


def test_me_success_with_dependency_override(sample_user: UserResponse):
    """Scenario: protected route returns current user when auth is injected."""
    client = create_auth_test_client(sample_user, with_user_auth=True)

    # When: /me is requested with auth dependency override.
    response = client.get("/api/v1/auth/me")

    # Then: current user payload is returned.
    assert response.status_code == 200
    assert response.json()["id"] == sample_user.id


def test_logout_success_with_dependency_override(sample_user: UserResponse):
    """Scenario: logout route succeeds when current user dependency is provided."""
    client = create_auth_test_client(sample_user, with_user_auth=True)

    # When: logout is requested with dependency-injected current user.
    response = client.post("/api/v1/auth/logout")

    # Then: logout success message is returned.
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out."


def test_admin_user_role_stats_success(sample_admin_user: UserResponse):
    """Scenario: admin-only stats route returns aggregated role metrics for admin user."""
    client = create_auth_admin_test_client(sample_admin_user)

    # When: admin role requests role stats endpoint.
    response = client.get("/api/v1/auth/admin/user-role-stats")

    # Then: role stats payload is returned.
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_users"] == 51
    assert payload["admin_users"] == 1


def test_admin_user_role_stats_requires_admin_role(sample_user: UserResponse):
    """Scenario: admin-only stats route rejects non-admin role with domain permission error."""
    client = create_auth_test_client(sample_user, with_user_auth=True)

    # When: non-admin user requests admin stats endpoint.
    response = client.get("/api/v1/auth/admin/user-role-stats")

    # Then: insufficient-role domain error is returned.
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "INSUFFICIENT_ROLE"
