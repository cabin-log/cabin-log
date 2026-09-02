import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select

from app.core.db.session import get_db
from app.models.activity import Activity
from app.models.game import (
    GameData,
    RewardPackageCreate,
    RewardPackageCreateItem,
    RewardPackageItemType,
    RewardPackageResponse,
    RewardPackageSource,
    StackProfileResponse,
    StackProfilesResponse,
    StackProfileUpsert,
    StackRewardType,
)
from app.models.github import GitHubRepository, GitHubRepositoryLanguage

RECENT_ACTIVITY_WINDOW_DAYS = 30


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


def _slugify_language(language: str) -> str:
    return (
        language.strip()
        .lower()
        .replace("#", "sharp")
        .replace("+", "plus")
        .replace("/", "-")
        .replace(" ", "-")
    )
