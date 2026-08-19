import asyncio
import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config.settings import SETTINGS
from app.models.github import GitHubProfiles, GitHubRepositoryUpsert
from app.models.oauth import OAuthIdentityProfile, OAuthProvider
from app.models.user import Users
from app.services.auth import AuthService
from app.utils.token import create_access_token


async def _create_github_oauth_user() -> tuple[int, str]:
    profile = OAuthIdentityProfile(
        provider=OAuthProvider.GITHUB,
        provider_user_id="987654",
        email="octo@example.com",
        name="Octo Dev",
        email_verified=True,
        login="octodev",
        avatar_url="https://avatars.githubusercontent.com/u/987654?v=4",
        profile_url="https://github.com/octodev",
    )
    service = AuthService()
    user = await service._resolve_oauth_user(profile)
    await service._upsert_github_profile(user.id, profile)
    token = create_access_token(subject=str(user.id), email=user.email)
    return user.id, token


def _signed_headers(payload: dict, delivery_id: str = "delivery-001") -> dict[str, str]:
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(
        SETTINGS.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": delivery_id,
        "X-Hub-Signature-256": f"sha256={signature}",
        "Content-Type": "application/json",
    }


def _push_payload() -> dict:
    return {
        "ref": "refs/heads/main",
        "before": "abc123",
        "after": "def456",
        "sender": {
            "id": 987654,
            "login": "octodev",
        },
        "repository": {
            "id": 111222,
            "full_name": "octodev/cabin",
        },
        "pusher": {
            "name": "octodev",
            "email": "octo@example.com",
        },
        "head_commit": {
            "id": "def456",
            "timestamp": "2026-08-19T09:00:00Z",
        },
        "commits": [
            {"id": "def456", "message": "Add cabin log"},
        ],
    }


def _pull_request_payload(action: str = "opened", merged: bool = False) -> dict:
    return {
        "action": action,
        "sender": {
            "id": 987654,
            "login": "octodev",
        },
        "repository": {
            "id": 111222,
            "full_name": "octodev/cabin",
        },
        "pull_request": {
            "number": 42,
            "title": "Add cabin activity",
            "html_url": "https://github.com/octodev/cabin/pull/42",
            "updated_at": "2026-08-19T10:00:00Z",
            "merged": merged,
        },
    }


@pytest.mark.primary_data
def test_github_oauth_profile_can_be_viewed(integration_client: TestClient):
    """Scenario: GitHub OAuth identity data is persisted and exposed for the current user."""
    user_id, token = asyncio.run(_create_github_oauth_user())

    response = integration_client.get(
        "/api/v1/github/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == user_id
    assert payload["github_user_id"] == 987654
    assert payload["login"] == "octodev"
    assert payload["display_name"] == "Octo Dev"
    assert payload["avatar_url"].startswith("https://avatars.githubusercontent.com/")
    assert payload["profile_url"] == "https://github.com/octodev"


@pytest.mark.primary_data
def test_github_push_webhook_creates_activity_once(integration_client: TestClient):
    """Scenario: signed push webhook creates one Cabinlog activity and deduplicates delivery id."""
    original_secret = SETTINGS.GITHUB_WEBHOOK_SECRET
    object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", "webhook-test-secret")
    try:
        _user_id, token = asyncio.run(_create_github_oauth_user())
        payload = _push_payload()
        body = json.dumps(payload)

        first_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=body,
            headers=_signed_headers(payload),
        )
        assert first_response.status_code == 200
        assert first_response.json()["status"] == "created"
        assert first_response.json()["activity"]["type"] == "PUSH"

        duplicate_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=body,
            headers=_signed_headers(payload),
        )
        assert duplicate_response.status_code == 200
        assert duplicate_response.json()["status"] == "duplicate"

        activities_response = integration_client.get(
            "/api/v1/github/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert activities_response.status_code == 200
        activities = activities_response.json()
        assert len(activities) == 1
        assert activities[0]["repository_github_id"] == 111222
        assert activities[0]["repository_full_name"] == "octodev/cabin"
        assert activities[0]["github_delivery_id"] == "delivery-001"
        assert activities[0]["metadata"]["commit_count"] == 1
    finally:
        object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", original_secret)


@pytest.mark.primary_data
def test_github_pull_request_webhook_creates_pr_activities(integration_client: TestClient):
    """Scenario: signed pull_request webhooks create opened and merged activities."""
    original_secret = SETTINGS.GITHUB_WEBHOOK_SECRET
    object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", "webhook-test-secret")
    try:
        _user_id, token = asyncio.run(_create_github_oauth_user())

        opened_payload = _pull_request_payload(action="opened", merged=False)
        opened_headers = _signed_headers(opened_payload, delivery_id="delivery-pr-opened")
        opened_headers["X-GitHub-Event"] = "pull_request"
        opened_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(opened_payload),
            headers=opened_headers,
        )
        assert opened_response.status_code == 200
        assert opened_response.json()["activity"]["type"] == "PULL_REQUEST_OPENED"

        merged_payload = _pull_request_payload(action="closed", merged=True)
        merged_headers = _signed_headers(merged_payload, delivery_id="delivery-pr-merged")
        merged_headers["X-GitHub-Event"] = "pull_request"
        merged_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(merged_payload),
            headers=merged_headers,
        )
        assert merged_response.status_code == 200
        assert merged_response.json()["activity"]["type"] == "PULL_REQUEST_MERGED"

        activities_response = integration_client.get(
            "/api/v1/github/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert activities_response.status_code == 200
        activity_types = {activity["type"] for activity in activities_response.json()}
        assert "PULL_REQUEST_OPENED" in activity_types
        assert "PULL_REQUEST_MERGED" in activity_types
    finally:
        object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", original_secret)


@pytest.mark.primary_data
def test_github_repositories_and_stack_summary_can_be_viewed(integration_client: TestClient):
    """Scenario: repository language snapshots are exposed with stack ratios."""
    user_id, token = asyncio.run(_create_github_oauth_user())

    async def _seed_repositories() -> None:
        await GitHubProfiles.upsert_repositories(
            [
                GitHubRepositoryUpsert(
                    user_id=user_id,
                    github_repo_id=111222,
                    owner_login="octodev",
                    name="cabin",
                    full_name="octodev/cabin",
                    private=False,
                    html_url="https://github.com/octodev/cabin",
                    default_branch="main",
                    primary_language="Python",
                    languages={"Python": 900, "TypeScript": 100},
                ),
                GitHubRepositoryUpsert(
                    user_id=user_id,
                    github_repo_id=333444,
                    owner_login="octodev",
                    name="game-client",
                    full_name="octodev/game-client",
                    private=False,
                    html_url="https://github.com/octodev/game-client",
                    default_branch="main",
                    primary_language="TypeScript",
                    languages={"TypeScript": 1000},
                ),
            ]
        )

    asyncio.run(_seed_repositories())

    repositories_response = integration_client.get(
        "/api/v1/github/repositories",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert repositories_response.status_code == 200
    assert {repo["full_name"] for repo in repositories_response.json()} == {
        "octodev/cabin",
        "octodev/game-client",
    }

    stack_response = integration_client.get(
        "/api/v1/github/stack-summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stack_response.status_code == 200
    stack_payload = stack_response.json()
    assert stack_payload["total_bytes"] == 2000
    assert stack_payload["languages"][0]["language"] == "TypeScript"
    assert stack_payload["languages"][0]["bytes"] == 1100
    assert stack_payload["languages"][0]["ratio"] == 0.55


@pytest.mark.primary_data
def test_github_webhook_rejects_invalid_signature(integration_client: TestClient):
    """Scenario: webhook signature verification rejects tampered requests."""
    original_secret = SETTINGS.GITHUB_WEBHOOK_SECRET
    object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", "webhook-test-secret")
    try:
        response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(_push_payload()),
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "delivery-invalid",
                "X-Hub-Signature-256": "sha256=invalid",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"]["error"] == "GITHUB_WEBHOOK_INVALID_SIGNATURE"
    finally:
        object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", original_secret)


@pytest.mark.primary_data
def test_github_webhook_ignores_unsupported_event(integration_client: TestClient):
    """Scenario: unsupported GitHub events are acknowledged without activity creation."""
    original_secret = SETTINGS.GITHUB_WEBHOOK_SECRET
    object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", "webhook-test-secret")
    try:
        payload = _push_payload()
        headers = _signed_headers(payload, delivery_id="delivery-unsupported")
        headers["X-GitHub-Event"] = "issues"
        response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(payload),
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
        assert response.json()["reason"] == "unsupported_event"
    finally:
        object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", original_secret)


@pytest.mark.primary_data
def test_github_oauth_profile_updates_existing_identity(integration_client: TestClient):
    """Scenario: repeated GitHub OAuth login updates profile without creating another user."""
    _ = integration_client
    first_user_id, _token = asyncio.run(_create_github_oauth_user())

    async def _update_profile() -> None:
        profile = OAuthIdentityProfile(
            provider=OAuthProvider.GITHUB,
            provider_user_id="987654",
            email="octo@example.com",
            name="Octo Developer",
            email_verified=True,
            login="octodev-renamed",
            avatar_url="https://avatars.githubusercontent.com/u/987654?v=5",
            profile_url="https://github.com/octodev-renamed",
        )
        service = AuthService()
        user = await service._resolve_oauth_user(profile)
        await service._upsert_github_profile(user.id, profile)
        assert user.id == first_user_id

    asyncio.run(_update_profile())

    profile = asyncio.run(GitHubProfiles.get_profile_by_user_id(first_user_id))
    user = asyncio.run(Users.get_auth_user_by_identity("github", "987654"))
    assert user is not None
    assert profile is not None
    assert profile.login == "octodev-renamed"
    assert profile.display_name == "Octo Developer"
