import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.models.activity import Activities, ActivityCreate, ActivityType
from app.models.github import GitHubProfiles, GitHubRepositoryUpsert
from app.models.oauth import OAuthIdentityProfile, OAuthProvider
from app.services.auth import AuthService
from app.services.game import GameService
from app.utils.token import create_access_token


async def _create_github_oauth_user() -> tuple[int, str]:
    profile = OAuthIdentityProfile(
        provider=OAuthProvider.GITHUB,
        provider_user_id="246810",
        email="stacker@example.com",
        name="Stack Dev",
        email_verified=True,
        login="stackdev",
        avatar_url="https://avatars.githubusercontent.com/u/246810?v=4",
        profile_url="https://github.com/stackdev",
    )
    service = AuthService()
    user = await service._resolve_oauth_user(profile)
    await service._upsert_github_profile(user.id, profile)
    token = create_access_token(subject=str(user.id), email=user.email)
    return user.id, token


async def _seed_stack_activity(user_id: int) -> None:
    await GitHubProfiles.upsert_repositories(
        [
            GitHubRepositoryUpsert(
                user_id=user_id,
                github_repo_id=900001,
                owner_login="stackdev",
                name="python-cabin",
                full_name="stackdev/python-cabin",
                private=False,
                primary_language="Python",
                pushed_at=datetime(2026, 9, 1, 9, 0, tzinfo=UTC),
                languages={"Python": 1_100_000},
            ),
            GitHubRepositoryUpsert(
                user_id=user_id,
                github_repo_id=900002,
                owner_login="stackdev",
                name="ts-cabin",
                full_name="stackdev/ts-cabin",
                private=False,
                primary_language="TypeScript",
                pushed_at=datetime(2026, 9, 1, 9, 0, tzinfo=UTC),
                languages={"TypeScript": 260_000},
            ),
        ]
    )
    now = datetime.now(UTC)
    for index in range(15):
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.COMMIT,
                source="OAUTH_API",
                repository_github_id=900001,
                repository_full_name="stackdev/python-cabin",
                github_external_id=f"github:commit:python-{index}",
                occurred_at=now - timedelta(days=index % 5),
                metadata={"sha": f"python-{index}"},
            )
        )
    for index in range(5):
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.PULL_REQUEST_OPENED,
                source="OAUTH_API",
                repository_github_id=900002,
                repository_full_name="stackdev/ts-cabin",
                github_external_id=f"github:pull_request:ts-{index}:opened",
                occurred_at=now - timedelta(days=index),
                metadata={"number": index + 1},
            )
        )


@pytest.mark.primary_data
def test_stack_profiles_packages_and_claim_flow(integration_client: TestClient):
    """Scenario: GitHub snapshot data creates stack profiles, packages, and claimable rewards."""
    user_id, token = asyncio.run(_create_github_oauth_user())
    asyncio.run(_seed_stack_activity(user_id))

    first_packages = asyncio.run(GameService().refresh_after_github_sync(user_id=user_id))
    duplicate_packages = asyncio.run(GameService().refresh_after_github_sync(user_id=user_id))

    assert len(first_packages) == 5
    assert duplicate_packages == []

    stacks_response = integration_client.get(
        "/api/v1/game/stacks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stacks_response.status_code == 200
    stacks = {item["language"]: item for item in stacks_response.json()["items"]}
    assert stacks["Python"]["mastery_level"] == 3
    assert stacks["Python"]["tier"] == 3
    assert stacks["TypeScript"]["mastery_level"] == 2
    assert stacks["TypeScript"]["tier"] == 2

    packages_response = integration_client.get(
        "/api/v1/rewards/packages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert packages_response.status_code == 200
    packages = packages_response.json()
    assert len(packages) == 5
    assert {package["status"] for package in packages} == {"PENDING"}

    python_level_three = next(
        package
        for package in packages
        if package["metadata"]["language"] == "Python" and package["metadata"]["mastery_level"] == 3
    )
    claim_response = integration_client.post(
        f"/api/v1/rewards/packages/{python_level_three['id']}/claim",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert claim_response.status_code == 200
    claimed = claim_response.json()
    assert claimed["package"]["status"] == "CLAIMED"
    assert claimed["stack_rewards"][0]["reward_key"] == "stack.python-serpent"
    assert claimed["stack_rewards"][0]["reward_type"] == "ANIMAL"
    assert claimed["stack_rewards"][0]["source_language"] == "Python"
    assert claimed["stack_rewards"][0]["stack_reward_level"] == 3
    assert claimed["stack_rewards"][0]["stage"] == 2

    duplicate_claim_response = integration_client.post(
        f"/api/v1/rewards/packages/{python_level_three['id']}/claim",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert duplicate_claim_response.status_code == 409
    assert duplicate_claim_response.json()["detail"]["error"] == "REWARD_PACKAGE_ALREADY_CLAIMED"
