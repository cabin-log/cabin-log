import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.db.session import get_db
from app.models.activity import Activities, ActivityCreate, ActivityType
from app.models.game import StackRewardType, UserStackReward
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


async def _seed_owned_stack_reward(user_id: int) -> None:
    async with get_db() as db:
        db.add(
            UserStackReward(
                user_id=user_id,
                reward_key="stack.python-serpent",
                reward_type=StackRewardType.ANIMAL.value,
                source_language="Python",
                stage=1,
                stack_reward_level=1,
            )
        )
        await db.commit()


async def _seed_event_reward_activity(user_id: int) -> None:
    for index in range(10):
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.COMMIT,
                source="OAUTH_API",
                repository_full_name="stackdev/night-cabin",
                github_external_id=f"github:test:event:night-{index}",
                occurred_at=datetime(2026, 8, 1, 1, index, tzinfo=UTC),
                metadata={"message": f"Night commit {index}"},
            )
        )
    for index in range(7):
        day = index + 2
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.PUSH,
                source="OAUTH_API",
                repository_full_name="stackdev/morning-cabin",
                github_external_id=f"github:test:event:morning-{index}",
                occurred_at=datetime(2026, 8, day, 6, 0, tzinfo=UTC),
                metadata={"ref": "refs/heads/main"},
            )
        )
    await Activities.create_activity_once(
        ActivityCreate(
            user_id=user_id,
            type=ActivityType.PUSH,
            source="OAUTH_API",
            repository_full_name="stackdev/weekend-cabin",
            github_external_id="github:test:event:weekend-extra",
            occurred_at=datetime(2026, 8, 9, 6, 0, tzinfo=UTC),
            metadata={"ref": "refs/heads/main"},
        )
    )
    for index in range(20):
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.REVIEW,
                source="OAUTH_API",
                repository_full_name="stackdev/review-cabin",
                github_external_id=f"github:test:event:review-{index}",
                occurred_at=datetime(2026, 8, 10, 10, index, tzinfo=UTC),
                metadata={"title": f"Review cabin change {index}"},
            )
        )
    for index in range(3):
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.RELEASE,
                source="OAUTH_API",
                repository_full_name="stackdev/release-cabin",
                github_external_id=f"github:test:event:release-{index}",
                occurred_at=datetime(2026, 8, 11, 9, index, tzinfo=UTC),
                metadata={"tag": f"v1.0.{index}"},
            )
        )
    for index in range(15):
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.ISSUE,
                source="OAUTH_API",
                repository_full_name="stackdev/bugfix-cabin",
                github_external_id=f"github:test:event:bugfix-{index}",
                occurred_at=datetime(2026, 8, 12, 12, index, tzinfo=UTC),
                metadata={"title": f"Fix cabin bug {index}", "state": "closed"},
            )
        )
    for index in range(10):
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.COMMIT,
                source="OAUTH_API",
                repository_full_name="stackdev/docs-cabin",
                github_external_id=f"github:test:event:docs-{index}",
                occurred_at=datetime(2026, 8, 13, 13, index, tzinfo=UTC),
                metadata={"message": f"Update README docs {index}", "files": ["README.md"]},
            )
        )
    for index in range(10):
        await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.PULL_REQUEST_OPENED,
                source="OAUTH_API",
                repository_full_name="stackdev/collab-cabin",
                github_external_id=f"github:test:event:collab-{index}",
                occurred_at=datetime(2026, 8, 14, 14, index, tzinfo=UTC),
                metadata={"title": f"Collaborate on cabin {index}"},
            )
        )


@pytest.mark.primary_data
def test_stack_profiles_packages_and_claim_flow(integration_client: TestClient):
    """Scenario: GitHub snapshot data creates stack profiles, packages, and claimable rewards."""
    user_id, token = asyncio.run(_create_github_oauth_user())
    asyncio.run(_seed_stack_activity(user_id))

    first_packages = asyncio.run(GameService().refresh_after_github_sync(user_id=user_id))
    duplicate_packages = asyncio.run(GameService().refresh_after_github_sync(user_id=user_id))

    assert len(first_packages) >= 5
    assert duplicate_packages == []
    assert sum(1 for package in first_packages if package.source == "DAILY_REWARD") == 1
    assert (
        sum(
            1
            for package in first_packages
            if package.source == "ACHIEVEMENT"
            and package.metadata.get("reward_key") == "event.first-sync-compass"
        )
        == 1
    )
    onboarding_package = next(
        package for package in first_packages if package.metadata.get("grant_type") == "onboarding"
    )
    assert onboarding_package.source == "GITHUB_SYNC"
    assert onboarding_package.metadata["activity_scope"] == "github_history"
    assert onboarding_package.metadata["total_activity_count"] == 20
    onboarding_items = {item.item_type: item for item in onboarding_package.items}
    assert onboarding_items["CURRENCY"].item_key == "coins"
    assert onboarding_items["FOOD"].item_key == "basic_feed"
    assert onboarding_items["PET_EXP"].item_key == "pet_exp"

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
    assert len(packages) >= 5
    assert {package["status"] for package in packages} == {"PENDING"}
    assert sum(1 for package in packages if package["source"] == "DAILY_REWARD") == 1
    assert (
        sum(
            1
            for package in packages
            if package["source"] == "ACHIEVEMENT"
            and package["metadata"].get("reward_key") == "event.first-sync-compass"
        )
        == 1
    )
    assert (
        sum(1 for package in packages if package["metadata"].get("grant_type") == "onboarding") == 1
    )

    python_origin = next(
        package
        for package in packages
        if package["metadata"].get("language") == "Python"
        and package["metadata"].get("mastery_level") == 1
    )
    claim_response = integration_client.post(
        f"/api/v1/rewards/packages/{python_origin['id']}/claim",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert claim_response.status_code == 200
    claimed = claim_response.json()
    assert claimed["package"]["status"] == "CLAIMED"
    assert claimed["stack_rewards"][0]["reward_key"] == "stack.python-serpent"
    assert claimed["stack_rewards"][0]["reward_type"] == "ANIMAL"
    assert claimed["stack_rewards"][0]["source_language"] == "Python"
    assert claimed["stack_rewards"][0]["stack_reward_level"] == 1
    assert claimed["stack_rewards"][0]["stage"] == 1

    typescript_origin = next(
        package
        for package in packages
        if package["metadata"].get("language") == "TypeScript"
        and package["metadata"].get("mastery_level") == 1
    )
    typescript_claim_response = integration_client.post(
        f"/api/v1/rewards/packages/{typescript_origin['id']}/claim",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert typescript_claim_response.status_code == 200

    inventory_response = integration_client.get(
        "/api/v1/game/inventory",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert inventory_response.status_code == 200
    inventory = inventory_response.json()
    assert inventory["supplies"] == []
    assert [item["reward_key"] for item in inventory["furniture"]] == ["stack.terminal-desk"]
    assert [item["reward_key"] for item in inventory["pet_logs"]] == [
        "default.octocat",
        "stack.python-serpent",
    ]

    collection_response = integration_client.get(
        "/api/v1/game/collection",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert collection_response.status_code == 200
    collection = collection_response.json()
    collection_furniture = {item["reward_key"]: item for item in collection["furniture"]}
    collection_pet_logs = {item["reward_key"]: item for item in collection["pet_logs"]}
    assert collection_furniture["stack.terminal-desk"]["owned"] is True
    assert collection_furniture["stack.terminal-desk"]["asset_key"] == "typescript-terminal-desk"
    assert collection_furniture["stack.forge-bench"]["owned"] is False
    assert collection_furniture["stack.forge-bench"]["required_bytes"] == 50_000
    assert collection_furniture["stack.browser-console-table"]["owned"] is False
    assert collection_furniture["event.night-owl-bed"]["condition_key"] == "night_owl_commits"
    assert collection_furniture["event.first-sync-compass"]["owned"] is False
    assert collection_pet_logs["stack.python-serpent"]["owned"] is True
    assert collection_pet_logs["stack.coffee-sprout"]["owned"] is False
    assert collection_pet_logs["stack.night-fox"]["required_recent_activity_count"] == 10
    assert collection_pet_logs["event.streak-spark"]["condition_key"] == "activity_streak"

    duplicate_claim_response = integration_client.post(
        f"/api/v1/rewards/packages/{python_origin['id']}/claim",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert duplicate_claim_response.status_code == 409
    assert duplicate_claim_response.json()["detail"]["error"] == "REWARD_PACKAGE_ALREADY_CLAIMED"


@pytest.mark.primary_data
def test_event_reward_sync_creates_achievement_packages(integration_client: TestClient):
    """Scenario: stored GitHub activity unlocks event reward packages once."""
    user_id, token = asyncio.run(_create_github_oauth_user())
    asyncio.run(_seed_event_reward_activity(user_id))

    sync_response = integration_client.post(
        "/api/v1/game/rewards/sync",
        headers={"Authorization": f"Bearer {token}"},
    )
    duplicate_sync_response = integration_client.post(
        "/api/v1/game/rewards/sync",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert sync_response.status_code == 200
    assert duplicate_sync_response.status_code == 200
    packages = sync_response.json()
    event_packages = [
        package for package in packages if package["metadata"].get("grant_type") == "event_reward"
    ]
    expected_event_reward_keys = {
        "event.night-owl-bed",
        "event.morning-kettle",
        "event.review-lamp",
        "event.release-banner",
        "event.bugfix-toolbox",
        "event.weekend-cushion",
        "event.docs-scroll",
        "event.first-sync-compass",
        "event.streak-spark",
        "event.mentor-orb",
    }
    actual_event_reward_keys = {package["metadata"]["reward_key"] for package in event_packages}
    assert actual_event_reward_keys == expected_event_reward_keys, (
        expected_event_reward_keys - actual_event_reward_keys
    )
    assert {package["source"] for package in event_packages} == {"ACHIEVEMENT"}
    assert duplicate_sync_response.json() == []

    night_package = next(
        package
        for package in event_packages
        if package["metadata"]["reward_key"] == "event.night-owl-bed"
    )
    assert night_package["metadata"]["condition_key"] == "night_owl_commits"
    assert night_package["metadata"]["threshold"] == 10
    assert night_package["metadata"]["progress"] >= 10

    claim_response = integration_client.post(
        f"/api/v1/rewards/packages/{night_package['id']}/claim",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert claim_response.status_code == 200
    claimed = claim_response.json()
    assert claimed["stack_rewards"][0]["reward_key"] == "event.night-owl-bed"
    assert claimed["stack_rewards"][0]["reward_type"] == "FURNITURE"
    assert claimed["stack_rewards"][0]["source_language"] == "Achievement"

    collection_response = integration_client.get(
        "/api/v1/game/collection",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert collection_response.status_code == 200
    collection_furniture = {
        item["reward_key"]: item for item in collection_response.json()["furniture"]
    }
    assert collection_furniture["event.night-owl-bed"]["owned"] is True


@pytest.mark.primary_data
def test_game_settings_and_daily_activity_summary_use_timezone_cutoff(
    integration_client: TestClient,
):
    """Scenario: daily summaries use the user's timezone and 05:00 local cutoff."""
    user_id, token = asyncio.run(_create_github_oauth_user())

    settings_response = integration_client.get(
        "/api/v1/game/settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert settings_response.status_code == 200
    assert settings_response.json()["timezone"] == "UTC"
    assert settings_response.json()["daily_cutoff_hour"] == 5

    invalid_settings_response = integration_client.patch(
        "/api/v1/game/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={"timezone": "Not/AZone"},
    )
    assert invalid_settings_response.status_code == 422

    updated_settings_response = integration_client.patch(
        "/api/v1/game/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={"timezone": "Asia/Seoul"},
    )
    assert updated_settings_response.status_code == 200
    assert updated_settings_response.json()["timezone"] == "Asia/Seoul"

    activities = [
        (
            "excluded-before-cutoff",
            ActivityType.COMMIT,
            datetime(2026, 9, 1, 19, 59, tzinfo=UTC),
        ),
        (
            "included-cutoff-start",
            ActivityType.COMMIT,
            datetime(2026, 9, 1, 20, 0, tzinfo=UTC),
        ),
        (
            "included-before-next-cutoff",
            ActivityType.COMMIT,
            datetime(2026, 9, 2, 19, 59, tzinfo=UTC),
        ),
        (
            "included-merged-pr",
            ActivityType.PULL_REQUEST_MERGED,
            datetime(2026, 9, 2, 12, 0, tzinfo=UTC),
        ),
        (
            "excluded-next-cutoff",
            ActivityType.ISSUE,
            datetime(2026, 9, 2, 20, 0, tzinfo=UTC),
        ),
    ]
    for external_id, activity_type, occurred_at in activities:
        asyncio.run(
            Activities.create_activity_once(
                ActivityCreate(
                    user_id=user_id,
                    type=activity_type,
                    source="OAUTH_API",
                    github_external_id=f"github:test:{external_id}",
                    occurred_at=occurred_at,
                    metadata={"external_id": external_id},
                )
            )
        )

    summary_response = integration_client.get(
        "/api/v1/game/activity/daily-summary?reward_date=2026-09-02",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["reward_date"] == "2026-09-02"
    assert summary["timezone"] == "Asia/Seoul"
    assert summary["daily_cutoff_hour"] == 5
    assert summary["window_start"] == "2026-09-01T20:00:00Z"
    assert summary["window_end"] == "2026-09-02T20:00:00Z"
    assert summary["total_activity_count"] == 3
    assert summary["total_points"] == 43
    assert summary["raw_coins"] == 41
    assert summary["coins"] == 41
    assert summary["food"] == 3
    assert summary["pet_exp"] == 172
    items = {item["activity_type"]: item for item in summary["items"]}
    assert items["COMMIT"] == {
        "activity_type": "COMMIT",
        "count": 2,
        "points": 8,
        "raw_coins": 6,
        "capped_coins": 6,
    }
    assert items["PULL_REQUEST_MERGED"] == {
        "activity_type": "PULL_REQUEST_MERGED",
        "count": 1,
        "points": 35,
        "raw_coins": 35,
        "capped_coins": 35,
    }

    reward_response = integration_client.post(
        "/api/v1/game/activity/daily-reward?reward_date=2026-09-02",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reward_response.status_code == 200
    reward = reward_response.json()
    assert reward["reward_date"] == "2026-09-02"
    assert reward["created"] is True
    assert reward["package"]["source"] == "DAILY_REWARD"
    assert reward["package"]["status"] == "PENDING"
    assert reward["package"]["metadata"]["reward_date"] == "2026-09-02"
    reward_items = {item["item_type"]: item for item in reward["package"]["items"]}
    assert reward_items["CURRENCY"]["item_key"] == "coins"
    assert reward_items["CURRENCY"]["quantity"] == 41
    assert reward_items["FOOD"]["item_key"] == "basic_feed"
    assert reward_items["FOOD"]["quantity"] == 3
    assert reward_items["PET_EXP"]["item_key"] == "pet_exp"
    assert reward_items["PET_EXP"]["quantity"] == 172
    assert "MATERIAL" not in reward_items

    duplicate_reward_response = integration_client.post(
        "/api/v1/game/activity/daily-reward?reward_date=2026-09-02",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert duplicate_reward_response.status_code == 200
    duplicate_reward = duplicate_reward_response.json()
    assert duplicate_reward["created"] is False
    assert duplicate_reward["package"]["id"] == reward["package"]["id"]

    claim_response = integration_client.post(
        f"/api/v1/rewards/packages/{reward['package']['id']}/claim",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert claim_response.status_code == 200
    claimed = claim_response.json()
    assert claimed["package"]["status"] == "CLAIMED"
    assert claimed["wallet"]["coins"] == 41
    claimed_inventory = {item["item_key"]: item for item in claimed["inventory"]}
    assert claimed_inventory["basic_feed"]["quantity"] == 3
    assert claimed_inventory["pet_exp"]["quantity"] == 172

    state_response = integration_client.get(
        "/api/v1/game/state",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["settings"]["timezone"] == "Asia/Seoul"
    assert state["today"]["timezone"] == "Asia/Seoul"
    assert state["wallet"]["coins"] == 41
    state_inventory = {item["item_key"]: item for item in state["inventory"]}
    assert state_inventory["basic_feed"]["quantity"] == 3
    assert state_inventory["pet_exp"]["quantity"] == 172
    assert state["pending_packages"] == []


@pytest.mark.primary_data
def test_default_daily_reward_date_uses_last_completed_window(
    integration_client: TestClient,
):
    """Scenario: omitted reward dates settle the last completed daily window."""
    user_id, token = asyncio.run(_create_github_oauth_user())
    asyncio.run(
        Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.COMMIT,
                source="OAUTH_API",
                github_external_id="github:test:settled-yesterday",
                occurred_at=datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
                metadata={"external_id": "settled-yesterday"},
            )
        )
    )

    updated_settings_response = integration_client.patch(
        "/api/v1/game/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={"timezone": "UTC"},
    )
    assert updated_settings_response.status_code == 200

    service = GameService()
    assert (
        service._resolve_reward_date(
            now=datetime(2026, 9, 6, 6, 0, tzinfo=UTC),
            timezone=UTC,
        )
        == datetime(2026, 9, 5, tzinfo=UTC).date()
    )
    assert (
        service._resolve_reward_date(
            now=datetime(2026, 9, 6, 4, 0, tzinfo=UTC),
            timezone=UTC,
        )
        == datetime(2026, 9, 4, tzinfo=UTC).date()
    )


@pytest.mark.primary_data
def test_game_reward_sync_endpoint_creates_onboarding_package(
    integration_client: TestClient,
):
    """Scenario: cabin reward sync creates one onboarding package from stored history."""
    user_id, token = asyncio.run(_create_github_oauth_user())
    asyncio.run(
        Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.COMMIT,
                source="OAUTH_API",
                github_external_id="github:test:onboarding-history",
                occurred_at=datetime(2026, 8, 19, 9, 0, tzinfo=UTC),
                metadata={"external_id": "onboarding-history"},
            )
        )
    )

    sync_response = integration_client.post(
        "/api/v1/game/rewards/sync",
        headers={"Authorization": f"Bearer {token}"},
    )
    duplicate_sync_response = integration_client.post(
        "/api/v1/game/rewards/sync",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert sync_response.status_code == 200
    assert duplicate_sync_response.status_code == 200
    synced_packages = sync_response.json()
    assert len(synced_packages) == 2
    onboarding_package = next(
        package
        for package in synced_packages
        if package["metadata"].get("grant_type") == "onboarding"
    )
    event_package = next(
        package
        for package in synced_packages
        if package["metadata"].get("grant_type") == "event_reward"
    )
    assert onboarding_package["source"] == "GITHUB_SYNC"
    assert onboarding_package["metadata"]["total_activity_count"] == 1
    assert event_package["source"] == "ACHIEVEMENT"
    assert event_package["metadata"]["reward_key"] == "event.first-sync-compass"
    assert duplicate_sync_response.json() == []


@pytest.mark.primary_data
def test_cabin_placement_flow_persists_user_adjusted_positions(
    integration_client: TestClient,
):
    """Scenario: players can place, move, and remove owned cabin objects."""
    user_id, token = asyncio.run(_create_github_oauth_user())

    cabin_response = integration_client.get(
        "/api/v1/game/cabin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cabin_response.status_code == 200
    cabin = cabin_response.json()
    assert cabin["width"] == 12
    assert cabin["depth"] == 12
    assert cabin["tile_width"] == 60
    assert cabin["tile_height"] == 30
    assert cabin["tile_z_height"] == 46
    assert cabin["placements"] == [
        {
            "id": cabin["placements"][0]["id"],
            "object_type": "SYSTEM",
            "object_key": "system.dev-board",
            "x": 0,
            "y": 0,
            "z": 1,
            "rotation": 0,
            "width": 2,
            "depth": 1,
            "locked": True,
            "updated_at": cabin["placements"][0]["updated_at"],
        }
    ]

    unowned_response = integration_client.post(
        "/api/v1/game/cabin/placements",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "object_type": "STACK_REWARD",
            "object_key": "stack.python-serpent",
            "x": 2,
            "y": 2,
            "z": 0,
            "rotation": 0,
            "width": 1,
            "depth": 1,
        },
    )
    assert unowned_response.status_code == 403
    assert unowned_response.json()["detail"]["error"] == "CABIN_ITEM_NOT_OWNED"

    asyncio.run(_seed_owned_stack_reward(user_id))
    placement_response = integration_client.post(
        "/api/v1/game/cabin/placements",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "object_type": "STACK_REWARD",
            "object_key": "stack.python-serpent",
            "x": 2,
            "y": 2,
            "z": 0,
            "rotation": 90,
            "width": 1,
            "depth": 1,
        },
    )
    assert placement_response.status_code == 201
    placement = placement_response.json()
    assert placement["object_key"] == "stack.python-serpent"
    assert placement["x"] == 2
    assert placement["y"] == 2
    assert placement["rotation"] == 90
    assert placement["locked"] is False

    conflict_response = integration_client.post(
        "/api/v1/game/cabin/placements",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "object_type": "STACK_REWARD",
            "object_key": "stack.python-serpent",
            "x": 2,
            "y": 2,
            "z": 0,
            "rotation": 0,
            "width": 1,
            "depth": 1,
        },
    )
    assert conflict_response.status_code == 409
    assert conflict_response.json()["detail"]["error"] == "CABIN_PLACEMENT_CONFLICT"

    moved_response = integration_client.patch(
        f"/api/v1/game/cabin/placements/{placement['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"x": 3, "y": 4, "rotation": 180},
    )
    assert moved_response.status_code == 200
    moved = moved_response.json()
    assert moved["x"] == 3
    assert moved["y"] == 4
    assert moved["rotation"] == 180

    state_response = integration_client.get(
        "/api/v1/game/state",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert state_response.status_code == 200
    state_placements = state_response.json()["cabin"]["placements"]
    assert any(item["id"] == placement["id"] and item["x"] == 3 for item in state_placements)

    delete_response = integration_client.delete(
        f"/api/v1/game/cabin/placements/{placement['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    after_delete_response = integration_client.get(
        "/api/v1/game/cabin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert after_delete_response.status_code == 200
    assert all(item["id"] != placement["id"] for item in after_delete_response.json()["placements"])


@pytest.mark.primary_data
def test_github_user_receives_default_octocat_pet_log(integration_client: TestClient):
    """Scenario: GitHub-linked users receive the default Octocat pet log before placement."""
    _user_id, token = asyncio.run(_create_github_oauth_user())

    state_response = integration_client.get(
        "/api/v1/game/state",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert state_response.status_code == 200
    state = state_response.json()
    pet_logs = {item["reward_key"]: item for item in state["categorized_inventory"]["pet_logs"]}
    assert pet_logs["default.octocat"]["source_language"] == "GitHub"
    assert pet_logs["default.octocat"]["stack_reward_level"] == 1
    collection_pet_logs = {item["reward_key"]: item for item in state["collection"]["pet_logs"]}
    assert collection_pet_logs["default.octocat"]["owned"] is True
    assert collection_pet_logs["default.octocat"]["asset_key"] == "default-octocat"
    assert collection_pet_logs["default.octocat"]["condition_key"] == "github_account"

    placement_response = integration_client.post(
        "/api/v1/game/cabin/placements",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "object_type": "STACK_REWARD",
            "object_key": "default.octocat",
            "x": 6,
            "y": 6,
            "z": 0,
            "rotation": 0,
            "width": 1,
            "depth": 1,
        },
    )
    assert placement_response.status_code == 201
    placement = placement_response.json()
    assert placement["object_key"] == "default.octocat"
    assert placement["x"] == 6
    assert placement["y"] == 6
