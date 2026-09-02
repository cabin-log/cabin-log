import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select

from app.core.db.session import get_db
from app.models.activity import Activity, ActivityType
from app.models.game import (
    CabinPlacementCreate,
    CabinPlacementResponse,
    CabinPlacementUpdate,
    CabinResponse,
    DailyActivitySummaryCaps,
    DailyActivitySummaryItem,
    DailyActivitySummaryResponse,
    DailyRewardPackageResponse,
    GameData,
    GameStateResponse,
    RewardPackageCreate,
    RewardPackageCreateItem,
    RewardPackageItemType,
    RewardPackageResponse,
    RewardPackageSource,
    RewardPackageStatus,
    StackProfileResponse,
    StackProfilesResponse,
    StackProfileUpsert,
    StackRewardType,
    UserGameSettingsResponse,
    UserGameSettingsUpdate,
    UserInventoryItemResponse,
    UserWalletResponse,
)
from app.models.github import GitHubRepository, GitHubRepositoryLanguage

RECENT_ACTIVITY_WINDOW_DAYS = 30
DAILY_CUTOFF_HOUR = 5

ACTIVITY_POINT_WEIGHTS: dict[ActivityType, int] = {
    ActivityType.COMMIT: 4,
    ActivityType.PUSH: 6,
    ActivityType.PULL_REQUEST_OPENED: 18,
    ActivityType.PULL_REQUEST_MERGED: 35,
    ActivityType.ISSUE: 10,
    ActivityType.REVIEW: 22,
    ActivityType.RELEASE: 45,
}

ACTIVITY_COIN_REWARDS: dict[ActivityType, int] = {
    ActivityType.COMMIT: 3,
    ActivityType.PUSH: 4,
    ActivityType.PULL_REQUEST_OPENED: 18,
    ActivityType.PULL_REQUEST_MERGED: 35,
    ActivityType.ISSUE: 10,
    ActivityType.REVIEW: 22,
    ActivityType.RELEASE: 50,
}

ACTIVITY_DAILY_COIN_CAPS: dict[ActivityType, int] = {
    ActivityType.COMMIT: 45,
    ActivityType.PUSH: 24,
    ActivityType.PULL_REQUEST_OPENED: 54,
    ActivityType.PULL_REQUEST_MERGED: 70,
    ActivityType.ISSUE: 40,
    ActivityType.REVIEW: 66,
    ActivityType.RELEASE: 100,
}


@dataclass(frozen=True)
class StackRewardDefinition:
    language: str
    reward_type: StackRewardType
    reward_key: str


STACK_REWARD_CATALOG: dict[str, StackRewardDefinition] = {
    "Python": StackRewardDefinition("Python", StackRewardType.ANIMAL, "stack.python-serpent"),
    "TypeScript": StackRewardDefinition(
        "TypeScript",
        StackRewardType.FURNITURE,
        "stack.terminal-desk",
    ),
    "Java": StackRewardDefinition("Java", StackRewardType.ANIMAL, "stack.coffee-sprout"),
    "Rust": StackRewardDefinition("Rust", StackRewardType.FURNITURE, "stack.forge-bench"),
    "Go": StackRewardDefinition("Go", StackRewardType.ANIMAL, "stack.cloud-helper"),
}


class GameService:
    async def get_user_settings(self, user_id: int) -> UserGameSettingsResponse:
        return await GameData.get_or_create_user_settings(user_id=user_id)

    async def update_user_settings(
        self,
        *,
        user_id: int,
        form: UserGameSettingsUpdate,
    ) -> UserGameSettingsResponse:
        return await GameData.update_user_settings(user_id=user_id, form=form)

    async def get_wallet(self, user_id: int) -> UserWalletResponse:
        return await GameData.get_or_create_wallet(user_id=user_id)

    async def list_inventory_items(self, user_id: int) -> list[UserInventoryItemResponse]:
        return await GameData.list_inventory_items(user_id=user_id)

    async def get_cabin(self, user_id: int) -> CabinResponse:
        return await GameData.get_or_create_cabin(user_id=user_id)

    async def create_cabin_placement(
        self,
        *,
        user_id: int,
        form: CabinPlacementCreate,
    ) -> CabinPlacementResponse:
        return await GameData.create_cabin_placement(user_id=user_id, form=form)

    async def update_cabin_placement(
        self,
        *,
        user_id: int,
        placement_id: int,
        form: CabinPlacementUpdate,
    ) -> CabinPlacementResponse:
        return await GameData.update_cabin_placement(
            user_id=user_id,
            placement_id=placement_id,
            form=form,
        )

    async def delete_cabin_placement(self, *, user_id: int, placement_id: int) -> None:
        await GameData.delete_cabin_placement(user_id=user_id, placement_id=placement_id)

    async def get_game_state(self, user_id: int) -> GameStateResponse:
        settings = await self.get_user_settings(user_id=user_id)
        today = await self.get_daily_activity_summary(user_id=user_id)
        wallet = await self.get_wallet(user_id=user_id)
        inventory = await self.list_inventory_items(user_id=user_id)
        cabin = await self.get_cabin(user_id=user_id)
        stack_profiles = await self.get_stack_profiles(user_id=user_id)
        stack_rewards = await GameData.list_stack_rewards(user_id=user_id)
        pending_packages = await GameData.list_reward_packages(
            user_id=user_id,
            status=RewardPackageStatus.PENDING,
        )
        return GameStateResponse(
            settings=settings,
            today=today,
            wallet=wallet,
            inventory=inventory,
            cabin=cabin,
            stack_profiles=stack_profiles,
            stack_rewards=stack_rewards,
            pending_packages=pending_packages,
        )

    async def get_daily_activity_summary(
        self,
        *,
        user_id: int,
        reward_date: date | None = None,
    ) -> DailyActivitySummaryResponse:
        settings = await self.get_user_settings(user_id=user_id)
        timezone = ZoneInfo(settings.timezone)
        resolved_reward_date = reward_date or self._resolve_reward_date(
            now=datetime.now(UTC),
            timezone=timezone,
        )
        window_start, window_end = self._resolve_daily_window(
            reward_date=resolved_reward_date,
            timezone=timezone,
        )
        counts = await GameData.list_daily_activity_counts(
            user_id=user_id,
            window_start=window_start,
            window_end=window_end,
        )
        items = [
            DailyActivitySummaryItem(
                activity_type=activity_type,
                count=count,
                points=ACTIVITY_POINT_WEIGHTS[activity_type] * count,
                raw_coins=ACTIVITY_COIN_REWARDS[activity_type] * count,
                capped_coins=min(
                    ACTIVITY_DAILY_COIN_CAPS[activity_type],
                    ACTIVITY_COIN_REWARDS[activity_type] * count,
                ),
            )
            for activity_type, count in sorted(counts.items(), key=lambda item: item[0].value)
        ]
        total_points = sum(item.points for item in items)
        raw_coins = sum(item.raw_coins for item in items)
        capped_type_coins = sum(item.capped_coins for item in items)
        caps = DailyActivitySummaryCaps()
        merged_pr_count = counts.get(ActivityType.PULL_REQUEST_MERGED, 0)
        return DailyActivitySummaryResponse(
            reward_date=resolved_reward_date,
            timezone=settings.timezone,
            daily_cutoff_hour=DAILY_CUTOFF_HOUR,
            window_start=window_start,
            window_end=window_end,
            total_activity_count=sum(counts.values()),
            total_points=total_points,
            raw_coins=raw_coins,
            coins=min(caps.coins, capped_type_coins),
            food=min(caps.food, total_points // 12),
            pet_exp=min(caps.pet_exp, total_points * 4),
            growth_material=min(caps.growth_material, merged_pr_count),
            caps=caps,
            items=items,
        )

    async def create_daily_reward_package(
        self,
        *,
        user_id: int,
        reward_date: date | None = None,
    ) -> DailyRewardPackageResponse:
        summary = await self.get_daily_activity_summary(
            user_id=user_id,
            reward_date=reward_date,
        )
        if summary.total_activity_count <= 0:
            return DailyRewardPackageResponse(
                reward_date=summary.reward_date,
                created=False,
                package=None,
                summary=summary,
            )

        grant_key = f"daily:{summary.reward_date.isoformat()}:github-activity"
        grant, created = await GameData.create_grant_once(
            user_id=user_id,
            grant_key=grant_key,
            source=RewardPackageSource.DAILY_REWARD,
        )
        if not created:
            return DailyRewardPackageResponse(
                reward_date=summary.reward_date,
                created=False,
                package=await GameData.get_package_by_grant_id(grant_id=grant.id),
                summary=summary,
            )

        items: list[RewardPackageCreateItem] = []
        if summary.coins > 0:
            items.append(
                RewardPackageCreateItem(
                    item_type=RewardPackageItemType.CURRENCY,
                    item_key="coins",
                    quantity=summary.coins,
                )
            )
        if summary.food > 0:
            items.append(
                RewardPackageCreateItem(
                    item_type=RewardPackageItemType.FOOD,
                    item_key="basic_feed",
                    quantity=summary.food,
                )
            )
        if summary.pet_exp > 0:
            items.append(
                RewardPackageCreateItem(
                    item_type=RewardPackageItemType.PET_EXP,
                    item_key="pet_exp",
                    quantity=summary.pet_exp,
                )
            )
        if summary.growth_material > 0:
            items.append(
                RewardPackageCreateItem(
                    item_type=RewardPackageItemType.MATERIAL,
                    item_key="growth_crystal",
                    quantity=summary.growth_material,
                )
            )

        package = await GameData.create_package_once(
            RewardPackageCreate(
                user_id=user_id,
                grant_id=grant.id,
                source=RewardPackageSource.DAILY_REWARD,
                title=f"{summary.reward_date.isoformat()} activity package",
                description="Daily GitHub activity rewards are ready.",
                metadata={
                    "reward_date": summary.reward_date.isoformat(),
                    "timezone": summary.timezone,
                    "daily_cutoff_hour": summary.daily_cutoff_hour,
                    "total_activity_count": summary.total_activity_count,
                    "total_points": summary.total_points,
                },
                items=items,
            )
        )
        return DailyRewardPackageResponse(
            reward_date=summary.reward_date,
            created=package is not None,
            package=package,
            summary=summary,
        )

    async def refresh_after_github_sync(self, user_id: int) -> list[RewardPackageResponse]:
        profiles = await self.recalculate_stack_profiles(user_id=user_id)
        return await self.generate_stack_reward_packages(
            user_id=user_id,
            profiles=profiles.items,
        )

    async def get_stack_profiles(self, user_id: int) -> StackProfilesResponse:
        return await GameData.list_stack_profiles(user_id=user_id)

    async def recalculate_stack_profiles(self, user_id: int) -> StackProfilesResponse:
        now = datetime.now(UTC)
        since = now - timedelta(days=RECENT_ACTIVITY_WINDOW_DAYS)
        language_bytes, language_repository_ids = await self._load_language_volume(user_id)
        recent_counts, active_days = await self._load_recent_activity_stats(
            user_id=user_id,
            since=since,
        )
        total_bytes = sum(language_bytes.values())
        profiles = [
            StackProfileUpsert(
                user_id=user_id,
                language=language,
                total_bytes=bytes_count,
                ratio=(bytes_count / total_bytes) if total_bytes else 0,
                repository_count=len(language_repository_ids.get(language, set())),
                recent_activity_count=recent_counts.get(language, 0),
                active_days_30d=len(active_days.get(language, set())),
                score=self._calculate_stack_score(
                    total_bytes=bytes_count,
                    ratio=(bytes_count / total_bytes) if total_bytes else 0,
                    recent_activity_count=recent_counts.get(language, 0),
                    repository_count=len(language_repository_ids.get(language, set())),
                ),
                tier=self._calculate_tier(
                    total_bytes=bytes_count,
                    recent_activity_count=recent_counts.get(language, 0),
                ),
                mastery_level=self._calculate_mastery_level(
                    total_bytes=bytes_count,
                    recent_activity_count=recent_counts.get(language, 0),
                    active_days_30d=len(active_days.get(language, set())),
                ),
                calculated_at=now,
            )
            for language, bytes_count in sorted(
                language_bytes.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]
        return StackProfilesResponse(
            items=await GameData.upsert_stack_profiles(user_id=user_id, profiles=profiles)
        )

    async def generate_stack_reward_packages(
        self,
        *,
        user_id: int,
        profiles: list[StackProfileResponse],
    ) -> list[RewardPackageResponse]:
        packages: list[RewardPackageResponse] = []
        for profile in profiles:
            definition = STACK_REWARD_CATALOG.get(profile.language)
            if definition is None or profile.mastery_level <= 0:
                continue
            for level in range(1, profile.mastery_level + 1):
                grant_key = (
                    f"stack_reward_upgrade:{_slugify_language(profile.language)}:"
                    f"level:{level}:{definition.reward_key}"
                )
                grant, created = await GameData.create_grant_once(
                    user_id=user_id,
                    grant_key=grant_key,
                    source=RewardPackageSource.GITHUB_SYNC,
                )
                if not created:
                    continue
                package = await GameData.create_package_once(
                    RewardPackageCreate(
                        user_id=user_id,
                        grant_id=grant.id,
                        source=RewardPackageSource.GITHUB_SYNC,
                        title=self._build_stack_package_title(
                            language=profile.language,
                            level=level,
                        ),
                        description=(f"{profile.language} stack reward level {level} is ready."),
                        metadata={
                            "language": profile.language,
                            "mastery_level": level,
                            "reward_key": definition.reward_key,
                            "reward_type": definition.reward_type.value,
                        },
                        items=[
                            RewardPackageCreateItem(
                                item_type=RewardPackageItemType.STACK_REWARD_UPGRADE,
                                item_key=definition.reward_key,
                                quantity=1,
                                metadata={
                                    "language": profile.language,
                                    "mastery_level": level,
                                    "reward_key": definition.reward_key,
                                    "reward_type": definition.reward_type.value,
                                },
                            )
                        ],
                    )
                )
                if package is not None:
                    packages.append(package)
        return packages

    async def list_reward_packages(
        self,
        *,
        user_id: int,
    ) -> list[RewardPackageResponse]:
        return await GameData.list_reward_packages(user_id=user_id)

    async def claim_reward_package(self, *, user_id: int, package_id: int):
        return await GameData.claim_reward_package(user_id=user_id, package_id=package_id)

    async def _load_language_volume(
        self,
        user_id: int,
    ) -> tuple[dict[str, int], dict[str, set[int]]]:
        async with get_db() as db:
            result = await db.execute(
                select(
                    GitHubRepositoryLanguage.language,
                    GitHubRepositoryLanguage.bytes,
                    GitHubRepository.github_repo_id,
                )
                .join(
                    GitHubRepository,
                    GitHubRepository.id == GitHubRepositoryLanguage.repository_id,
                )
                .where(GitHubRepository.user_id == user_id)
            )
            language_bytes: dict[str, int] = {}
            language_repository_ids: dict[str, set[int]] = {}
            for language, byte_count, github_repo_id in result.all():
                language_bytes[language] = language_bytes.get(language, 0) + int(byte_count)
                language_repository_ids.setdefault(language, set()).add(int(github_repo_id))
            return language_bytes, language_repository_ids

    async def _load_recent_activity_stats(
        self,
        *,
        user_id: int,
        since: datetime,
    ) -> tuple[dict[str, int], dict[str, set[str]]]:
        async with get_db() as db:
            result = await db.execute(
                select(
                    Activity.occurred_at,
                    GitHubRepositoryLanguage.language,
                )
                .join(
                    GitHubRepository,
                    or_(
                        GitHubRepository.github_repo_id == Activity.repository_github_id,
                        GitHubRepository.full_name == Activity.repository_full_name,
                    ),
                )
                .join(
                    GitHubRepositoryLanguage,
                    GitHubRepositoryLanguage.repository_id == GitHubRepository.id,
                )
                .where(
                    Activity.user_id == user_id,
                    GitHubRepository.user_id == user_id,
                    Activity.occurred_at >= since,
                )
            )
            counts: dict[str, int] = {}
            active_days: dict[str, set[str]] = {}
            for occurred_at, language in result.all():
                counts[language] = counts.get(language, 0) + 1
                active_days.setdefault(language, set()).add(occurred_at.date().isoformat())
            return counts, active_days

    def _calculate_stack_score(
        self,
        *,
        total_bytes: int,
        ratio: float,
        recent_activity_count: int,
        repository_count: int,
    ) -> float:
        return round(
            math.log10(total_bytes + 1) * 20
            + ratio * 35
            + min(recent_activity_count, 30) * 3
            + min(repository_count, 10) * 2,
            4,
        )

    def _calculate_tier(self, *, total_bytes: int, recent_activity_count: int) -> int:
        if total_bytes >= 1_000_000 and recent_activity_count >= 15:
            return 3
        if total_bytes >= 250_000 and recent_activity_count >= 5:
            return 2
        if total_bytes >= 50_000 or recent_activity_count >= 10:
            return 1
        return 0

    def _calculate_mastery_level(
        self,
        *,
        total_bytes: int,
        recent_activity_count: int,
        active_days_30d: int,
    ) -> int:
        if total_bytes >= 10_000_000 and recent_activity_count >= 75 and active_days_30d >= 21:
            return 5
        if total_bytes >= 3_000_000 and recent_activity_count >= 30 and active_days_30d >= 7:
            return 4
        if total_bytes >= 1_000_000 and recent_activity_count >= 15:
            return 3
        if total_bytes >= 250_000 and recent_activity_count >= 5:
            return 2
        if total_bytes >= 50_000 or recent_activity_count >= 10:
            return 1
        return 0

    def _build_stack_package_title(self, *, language: str, level: int) -> str:
        if level == 1:
            return f"{language} origin package"
        if level == 3:
            return f"{language} evolution package"
        return f"{language} level {level} upgrade package"

    def _resolve_reward_date(self, *, now: datetime, timezone: ZoneInfo) -> date:
        local_time = now.astimezone(timezone)
        return (local_time - timedelta(hours=DAILY_CUTOFF_HOUR)).date()

    def _resolve_daily_window(
        self,
        *,
        reward_date: date,
        timezone: ZoneInfo,
    ) -> tuple[datetime, datetime]:
        local_start = datetime.combine(
            reward_date,
            time(hour=DAILY_CUTOFF_HOUR),
            tzinfo=timezone,
        )
        local_end = local_start + timedelta(days=1)
        return local_start.astimezone(UTC), local_end.astimezone(UTC)


def _slugify_language(language: str) -> str:
    return (
        language.strip()
        .lower()
        .replace("#", "sharp")
        .replace("+", "plus")
        .replace("/", "-")
        .replace(" ", "-")
    )
