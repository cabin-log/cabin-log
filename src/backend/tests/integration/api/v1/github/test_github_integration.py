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
from app.services import github as github_service_module
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


def _signed_headers(
    payload: dict,
    delivery_id: str = "delivery-001",
    event_name: str = "push",
) -> dict[str, str]:
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(
        SETTINGS.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-GitHub-Event": event_name,
        "X-GitHub-Delivery": delivery_id,
        "X-Hub-Signature-256": f"sha256={signature}",
        "Content-Type": "application/json",
    }


def _push_payload() -> dict:
    return {
        "ref": "refs/heads/main",
        "before": "abc123",
        "after": "def456",
        "installation": {
            "id": 555666,
        },
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
        "installation": {
            "id": 555666,
        },
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


def _installation_payload(action: str = "created") -> dict:
    return {
        "action": action,
        "installation": {
            "id": 555666,
            "account": {
                "id": 987654,
                "login": "octodev",
                "type": "User",
            },
            "target_type": "User",
            "repository_selection": "selected",
        },
        "repositories": [
            {
                "id": 111222,
                "name": "cabin",
                "full_name": "octodev/cabin",
                "private": False,
                "html_url": "https://github.com/octodev/cabin",
                "default_branch": "main",
                "language": "Python",
            }
        ],
        "sender": {
            "id": 987654,
            "login": "octodev",
        },
    }


def _installation_repositories_payload() -> dict:
    return {
        "action": "added",
        "installation": {
            "id": 555666,
            "account": {
                "id": 987654,
                "login": "octodev",
                "type": "User",
            },
            "target_type": "User",
            "repository_selection": "selected",
        },
        "repositories_added": [
            {
                "id": 333444,
                "name": "game-client",
                "full_name": "octodev/game-client",
                "private": False,
                "html_url": "https://github.com/octodev/game-client",
                "default_branch": "main",
                "language": "TypeScript",
            }
        ],
        "repositories_removed": [
            {
                "id": 111222,
                "name": "cabin",
                "full_name": "octodev/cabin",
            }
        ],
        "sender": {
            "id": 987654,
            "login": "octodev",
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
def test_github_app_install_url_uses_configured_slug(integration_client: TestClient):
    """Scenario: current user can fetch the configured GitHub App installation URL."""
    original_slug = SETTINGS.GITHUB_APP_SLUG
    object.__setattr__(SETTINGS, "GITHUB_APP_SLUG", "cabinlog-dev")
    try:
        _user_id, token = asyncio.run(_create_github_oauth_user())

        response = integration_client.get(
            "/api/v1/github/app/install-url",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "configured": True,
            "install_url": "https://github.com/apps/cabinlog-dev/installations/new",
        }
    finally:
        object.__setattr__(SETTINGS, "GITHUB_APP_SLUG", original_slug)


@pytest.mark.primary_data
def test_github_oauth_snapshot_sync_persists_repositories_and_activities(
    integration_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Scenario: OAuth API snapshot stores repos, languages, commits, PRs, and issues."""

    async def fake_fetch_authenticated_user_repositories(
        self: github_service_module.GitHubAPIClient,
    ) -> list[dict]:
        assert self.access_token == "oauth-token"
        return [
            {
                "id": 111222,
                "name": "cabin",
                "full_name": "octodev/cabin",
                "private": True,
                "html_url": "https://github.com/octodev/cabin",
                "default_branch": "main",
                "language": "Python",
                "owner": {"login": "octodev"},
                "pushed_at": "2026-08-19T08:00:00Z",
            }
        ]

    async def fake_fetch_repository_languages(
        self: github_service_module.GitHubAPIClient,
        full_name: str,
    ) -> dict[str, int]:
        assert self.access_token == "oauth-token"
        assert full_name == "octodev/cabin"
        return {"Python": 900, "TypeScript": 100}

    async def fake_fetch_repository_commits_by_author(
        self: github_service_module.GitHubAPIClient,
        *,
        full_name: str,
        author_login: str,
    ) -> list[dict]:
        assert self.access_token == "oauth-token"
        assert full_name == "octodev/cabin"
        assert author_login == "octodev"
        return [
            {
                "sha": "abc123",
                "html_url": "https://github.com/octodev/cabin/commit/abc123",
                "commit": {
                    "message": "Add cabin activity",
                    "author": {"date": "2026-08-19T09:00:00Z"},
                },
            }
        ]

    async def fake_search_user_pull_requests(
        self: github_service_module.GitHubAPIClient,
        *,
        author_login: str,
    ) -> list[dict]:
        assert self.access_token == "oauth-token"
        assert author_login == "octodev"
        return [
            {
                "id": 444555,
                "number": 42,
                "title": "Open cabin PR",
                "html_url": "https://github.com/octodev/cabin/pull/42",
                "state": "open",
                "created_at": "2026-08-19T10:00:00Z",
                "repository": {"id": 111222, "full_name": "octodev/cabin"},
            }
        ]

    async def fake_search_user_merged_pull_requests(
        self: github_service_module.GitHubAPIClient,
        *,
        author_login: str,
    ) -> list[dict]:
        assert self.access_token == "oauth-token"
        assert author_login == "octodev"
        return [
            {
                "id": 666777,
                "number": 43,
                "title": "Merge cabin PR",
                "html_url": "https://github.com/octodev/cabin/pull/43",
                "state": "closed",
                "closed_at": "2026-08-19T11:00:00Z",
                "repository_url": "https://api.github.com/repos/octodev/cabin",
            }
        ]

    async def fake_search_user_issues(
        self: github_service_module.GitHubAPIClient,
        *,
        author_login: str,
    ) -> list[dict]:
        assert self.access_token == "oauth-token"
        assert author_login == "octodev"
        return [
            {
                "id": 888999,
                "number": 7,
                "title": "Track cabin issue",
                "html_url": "https://github.com/octodev/cabin/issues/7",
                "state": "open",
                "created_at": "2026-08-19T12:00:00Z",
                "repository_url": "https://api.github.com/repos/octodev/cabin",
            }
        ]

    monkeypatch.setattr(
        github_service_module.GitHubAPIClient,
        "fetch_authenticated_user_repositories",
        fake_fetch_authenticated_user_repositories,
    )
    monkeypatch.setattr(
        github_service_module.GitHubAPIClient,
        "fetch_repository_languages",
        fake_fetch_repository_languages,
    )
    monkeypatch.setattr(
        github_service_module.GitHubAPIClient,
        "fetch_repository_commits_by_author",
        fake_fetch_repository_commits_by_author,
    )
    monkeypatch.setattr(
        github_service_module.GitHubAPIClient,
        "search_user_pull_requests",
        fake_search_user_pull_requests,
    )
    monkeypatch.setattr(
        github_service_module.GitHubAPIClient,
        "search_user_merged_pull_requests",
        fake_search_user_merged_pull_requests,
    )
    monkeypatch.setattr(
        github_service_module.GitHubAPIClient,
        "search_user_issues",
        fake_search_user_issues,
    )

    user_id, token = asyncio.run(_create_github_oauth_user())
    first_response = integration_client.post(
        "/api/v1/github/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={"access_token": "oauth-token"},
    )
    duplicate_response = integration_client.post(
        "/api/v1/github/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={"access_token": "oauth-token"},
    )

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 200
    assert first_response.json() == {
        "repository_count": 1,
        "created_activity_count": 4,
        "duplicate_activity_count": 0,
    }
    assert duplicate_response.json() == {
        "repository_count": 1,
        "created_activity_count": 0,
        "duplicate_activity_count": 4,
    }

    repositories_response = integration_client.get(
        "/api/v1/github/repositories",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert repositories_response.status_code == 200
    repositories = repositories_response.json()
    assert repositories[0]["full_name"] == "octodev/cabin"
    assert repositories[0]["languages"] == {"Python": 900, "TypeScript": 100}

    activities_response = integration_client.get(
        "/api/v1/github/activities",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert activities_response.status_code == 200
    activities = activities_response.json()
    assert len(activities) == 4
    activity_types = {activity["type"] for activity in activities}
    assert activity_types == {
        "COMMIT",
        "PULL_REQUEST_OPENED",
        "PULL_REQUEST_MERGED",
        "ISSUE",
    }
    assert {activity["source"] for activity in activities} == {"OAUTH_API"}
    assert all(activity["github_external_id"] for activity in activities)
    assert all(activity["repository_full_name"] == "octodev/cabin" for activity in activities)


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
        assert activities[0]["github_installation_id"] == 555666
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
        opened_headers = _signed_headers(
            opened_payload,
            delivery_id="delivery-pr-opened",
            event_name="pull_request",
        )
        opened_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(opened_payload),
            headers=opened_headers,
        )
        assert opened_response.status_code == 200
        assert opened_response.json()["activity"]["type"] == "PULL_REQUEST_OPENED"

        merged_payload = _pull_request_payload(action="closed", merged=True)
        merged_headers = _signed_headers(
            merged_payload,
            delivery_id="delivery-pr-merged",
            event_name="pull_request",
        )
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
def test_github_app_installation_webhook_links_repositories_and_activity(
    integration_client: TestClient,
):
    """Scenario: GitHub App installation events link repos and later activity by installation id."""
    original_secret = SETTINGS.GITHUB_WEBHOOK_SECRET
    object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", "webhook-test-secret")
    try:
        _user_id, token = asyncio.run(_create_github_oauth_user())

        installation_payload = _installation_payload()
        installation_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(installation_payload),
            headers=_signed_headers(
                installation_payload,
                delivery_id="delivery-installation-created",
                event_name="installation",
            ),
        )
        assert installation_response.status_code == 200
        assert installation_response.json()["status"] == "upserted"
        assert installation_response.json()["installation"]["github_installation_id"] == 555666
        assert installation_response.json()["repository_count"] == 1

        installations_response = integration_client.get(
            "/api/v1/github/installations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert installations_response.status_code == 200
        installations = installations_response.json()
        assert len(installations) == 1
        assert installations[0]["github_installation_id"] == 555666
        assert installations[0]["account_login"] == "octodev"

        repositories_response = integration_client.get(
            "/api/v1/github/repositories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert repositories_response.status_code == 200
        repositories = repositories_response.json()
        assert len(repositories) == 1
        assert repositories[0]["full_name"] == "octodev/cabin"
        assert repositories[0]["github_installation_id"] == 555666

        push_payload = _push_payload()
        push_payload["sender"] = {
            "id": 123123,
            "login": "repo-collaborator",
        }
        push_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(push_payload),
            headers=_signed_headers(
                push_payload,
                delivery_id="delivery-installation-push",
            ),
        )
        assert push_response.status_code == 200
        assert push_response.json()["status"] == "created"
        assert push_response.json()["activity"]["github_installation_id"] == 555666

        activities_response = integration_client.get(
            "/api/v1/github/activities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert activities_response.status_code == 200
        assert activities_response.json()[0]["github_delivery_id"] == "delivery-installation-push"
    finally:
        object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", original_secret)


@pytest.mark.primary_data
def test_github_app_installation_repositories_webhook_updates_selected_repos(
    integration_client: TestClient,
):
    """Scenario: GitHub App repository selection changes add and remove linked repositories."""
    original_secret = SETTINGS.GITHUB_WEBHOOK_SECRET
    object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", "webhook-test-secret")
    try:
        _user_id, token = asyncio.run(_create_github_oauth_user())

        installation_payload = _installation_payload()
        integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(installation_payload),
            headers=_signed_headers(
                installation_payload,
                delivery_id="delivery-installation-seed",
                event_name="installation",
            ),
        )

        selection_payload = _installation_repositories_payload()
        selection_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(selection_payload),
            headers=_signed_headers(
                selection_payload,
                delivery_id="delivery-installation-repositories",
                event_name="installation_repositories",
            ),
        )
        assert selection_response.status_code == 200
        assert selection_response.json()["status"] == "updated"
        assert selection_response.json()["repositories_added"] == 1
        assert selection_response.json()["repositories_removed"] == 1

        repositories_response = integration_client.get(
            "/api/v1/github/repositories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert repositories_response.status_code == 200
        repositories = repositories_response.json()
        assert {repo["full_name"] for repo in repositories} == {"octodev/game-client"}
        assert repositories[0]["github_installation_id"] == 555666
    finally:
        object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", original_secret)


@pytest.mark.primary_data
def test_github_app_installation_sync_repositories_uses_installation_token(
    integration_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Scenario: linked GitHub App installation can sync repositories using an installation token."""
    original_secret = SETTINGS.GITHUB_WEBHOOK_SECRET
    original_app_id = SETTINGS.GITHUB_APP_ID
    original_private_key = SETTINGS.GITHUB_APP_PRIVATE_KEY
    object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", "webhook-test-secret")
    object.__setattr__(SETTINGS, "GITHUB_APP_ID", "123456")
    object.__setattr__(SETTINGS, "GITHUB_APP_PRIVATE_KEY", "fake-private-key")

    async def fake_create_installation_access_token(
        self: github_service_module.GitHubAppClient,
        github_installation_id: int,
    ) -> str:
        _ = self
        assert github_installation_id == 555666
        return "installation-token"

    async def fake_fetch_installation_repositories(
        self: github_service_module.GitHubAPIClient,
    ) -> list[dict]:
        assert self.access_token == "installation-token"
        return [
            {
                "id": 777888,
                "name": "installed-cabin",
                "full_name": "octodev/installed-cabin",
                "private": True,
                "html_url": "https://github.com/octodev/installed-cabin",
                "default_branch": "main",
                "language": "Python",
                "owner": {"login": "octodev"},
                "pushed_at": "2026-08-20T09:00:00Z",
            }
        ]

    async def fake_fetch_repository_languages(
        self: github_service_module.GitHubAPIClient,
        full_name: str,
    ) -> dict[str, int]:
        assert self.access_token == "installation-token"
        assert full_name == "octodev/installed-cabin"
        return {"Python": 700, "Shell": 300}

    monkeypatch.setattr(
        github_service_module.GitHubAppClient,
        "create_installation_access_token",
        fake_create_installation_access_token,
    )
    monkeypatch.setattr(
        github_service_module.GitHubAPIClient,
        "fetch_installation_repositories",
        fake_fetch_installation_repositories,
    )
    monkeypatch.setattr(
        github_service_module.GitHubAPIClient,
        "fetch_repository_languages",
        fake_fetch_repository_languages,
    )

    try:
        _user_id, token = asyncio.run(_create_github_oauth_user())
        installation_payload = _installation_payload()
        integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(installation_payload),
            headers=_signed_headers(
                installation_payload,
                delivery_id="delivery-installation-sync-seed",
                event_name="installation",
            ),
        )

        response = integration_client.post(
            "/api/v1/github/installations/555666/sync-repositories",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["github_installation_id"] == 555666
        assert payload["repository_count"] == 1
        assert payload["repositories"][0]["full_name"] == "octodev/installed-cabin"
        assert payload["repositories"][0]["github_installation_id"] == 555666
        assert payload["repositories"][0]["languages"] == {"Python": 700, "Shell": 300}
    finally:
        object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", original_secret)
        object.__setattr__(SETTINGS, "GITHUB_APP_ID", original_app_id)
        object.__setattr__(SETTINGS, "GITHUB_APP_PRIVATE_KEY", original_private_key)


@pytest.mark.primary_data
def test_github_app_installation_deleted_marks_installation_deleted(
    integration_client: TestClient,
):
    """Scenario: GitHub App installation deleted event keeps audit row and marks it deleted."""
    original_secret = SETTINGS.GITHUB_WEBHOOK_SECRET
    object.__setattr__(SETTINGS, "GITHUB_WEBHOOK_SECRET", "webhook-test-secret")
    try:
        _user_id, token = asyncio.run(_create_github_oauth_user())

        installation_payload = _installation_payload()
        integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(installation_payload),
            headers=_signed_headers(
                installation_payload,
                delivery_id="delivery-installation-before-delete",
                event_name="installation",
            ),
        )

        deleted_payload = _installation_payload(action="deleted")
        deleted_response = integration_client.post(
            "/api/v1/webhooks/github",
            content=json.dumps(deleted_payload),
            headers=_signed_headers(
                deleted_payload,
                delivery_id="delivery-installation-deleted",
                event_name="installation",
            ),
        )
        assert deleted_response.status_code == 200
        assert deleted_response.json()["status"] == "deleted"

        installations_response = integration_client.get(
            "/api/v1/github/installations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert installations_response.status_code == 200
        installations = installations_response.json()
        assert len(installations) == 1
        assert installations[0]["deleted_at"] is not None
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
                    github_installation_id=555666,
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
                    github_installation_id=555666,
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
