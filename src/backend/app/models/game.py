from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    delete,
    func,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from app.core.db.session import Base, get_db
from app.core.error import GameErrorCode, GameException
from app.models.activity import Activity, ActivityType


class StackRewardType(StrEnum):
    ANIMAL = "ANIMAL"
    FURNITURE = "FURNITURE"


class RewardPackageSource(StrEnum):
    GITHUB_SYNC = "GITHUB_SYNC"
    DAILY_REWARD = "DAILY_REWARD"
    ACHIEVEMENT = "ACHIEVEMENT"


class RewardPackageStatus(StrEnum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    EXPIRED = "EXPIRED"


class RewardPackageItemType(StrEnum):
    STACK_REWARD_UPGRADE = "STACK_REWARD_UPGRADE"
    CURRENCY = "CURRENCY"
    FOOD = "FOOD"
    PET_EXP = "PET_EXP"
    MATERIAL = "MATERIAL"
    COSMETIC = "COSMETIC"


DEFAULT_USER_TIMEZONE = "UTC"


class UserGameSettings(Base):
    __tablename__ = "user_game_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(64), default=DEFAULT_USER_TIMEZONE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")


class UserStackProfile(Base):
    __tablename__ = "user_stack_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "language", name="uq_user_stack_profiles_user_language"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    total_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    ratio: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    repository_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recent_activity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_days_30d: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    tier: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mastery_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")


class RewardGrant(Base):
    __tablename__ = "reward_grants"
    __table_args__ = (UniqueConstraint("user_id", "grant_key", name="uq_reward_grants_user_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    grant_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    user = relationship("User")


class RewardPackage(Base):
    __tablename__ = "reward_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    grant_id: Mapped[int | None] = mapped_column(
        ForeignKey("reward_grants.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    source: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(60), default=RewardPackageStatus.PENDING.value, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    package_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    user = relationship("User")
    grant = relationship("RewardGrant")
    items = relationship(
        "RewardPackageItem",
        back_populates="package",
        cascade="all, delete-orphan",
    )


class RewardPackageItem(Base):
    __tablename__ = "reward_package_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(
        ForeignKey("reward_packages.id", ondelete="CASCADE"), nullable=False
    )
    item_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    item_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    package = relationship("RewardPackage", back_populates="items")


class UserStackReward(Base):
    __tablename__ = "user_stack_rewards"
    __table_args__ = (
        UniqueConstraint("user_id", "reward_key", name="uq_user_stack_rewards_user_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reward_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reward_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    source_language: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    stage: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    stack_reward_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    exp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_featured: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")


class UserWallet(Base):
    __tablename__ = "user_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")


class UserInventoryItem(Base):
    __tablename__ = "user_inventory_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "item_type",
            "item_key",
            name="uq_user_inventory_items_user_type_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    item_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    item_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")


class StackProfileUpsert(BaseModel):
    user_id: int
    language: str
    total_bytes: int
    ratio: float
    repository_count: int
    recent_activity_count: int
    active_days_30d: int
    score: float
    tier: int
    mastery_level: int
    calculated_at: datetime


class UserGameSettingsUpdate(BaseModel):
    timezone: str = Field(min_length=1, max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        normalized = value.strip()
        try:
            ZoneInfo(normalized)
        except ZoneInfoNotFoundError:
            raise ValueError("timezone must be a valid IANA timezone name.") from None
        return normalized


class UserGameSettingsResponse(BaseModel):
    timezone: str
    daily_cutoff_hour: int = 5
    updated_at: datetime

    class Config:
        from_attributes = True


class StackProfileResponse(BaseModel):
    language: str
    total_bytes: int
    ratio: float
    repository_count: int
    recent_activity_count: int
    active_days_30d: int
    score: float
    tier: int
    mastery_level: int
    calculated_at: datetime

    class Config:
        from_attributes = True


class StackProfilesResponse(BaseModel):
    items: list[StackProfileResponse] = Field(default_factory=list)


class DailyActivitySummaryItem(BaseModel):
    activity_type: ActivityType
    count: int
    points: int
    raw_coins: int
    capped_coins: int


class DailyActivitySummaryCaps(BaseModel):
    food: int = 10
    coins: int = 150
    pet_exp: int = 300
    growth_material: int = 3
    package_count: int = 1


class DailyActivitySummaryResponse(BaseModel):
    reward_date: date
    timezone: str
    daily_cutoff_hour: int
    window_start: datetime
    window_end: datetime
    total_activity_count: int
    total_points: int
    raw_coins: int
    coins: int
    food: int
    pet_exp: int
    growth_material: int
    caps: DailyActivitySummaryCaps = Field(default_factory=DailyActivitySummaryCaps)
    items: list[DailyActivitySummaryItem] = Field(default_factory=list)


class DailyRewardPackageResponse(BaseModel):
    reward_date: date
    created: bool
    package: "RewardPackageResponse | None" = None
    summary: DailyActivitySummaryResponse


class RewardPackageItemResponse(BaseModel):
    id: int
    item_type: RewardPackageItemType
    item_key: str
    quantity: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class RewardPackageResponse(BaseModel):
    id: int
    source: RewardPackageSource
    status: RewardPackageStatus
    title: str
    description: str | None = None
    created_at: datetime
    claimed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    items: list[RewardPackageItemResponse] = Field(default_factory=list)


class UserStackRewardResponse(BaseModel):
    reward_key: str
    reward_type: StackRewardType
    source_language: str
    stage: int
    stack_reward_level: int
    exp: int
    is_featured: bool
    updated_at: datetime


class UserWalletResponse(BaseModel):
    coins: int
    updated_at: datetime


class UserInventoryItemResponse(BaseModel):
    item_type: RewardPackageItemType
    item_key: str
    quantity: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime


class RewardPackageClaimResponse(BaseModel):
    package: RewardPackageResponse
    stack_rewards: list[UserStackRewardResponse] = Field(default_factory=list)
    wallet: UserWalletResponse | None = None
    inventory: list[UserInventoryItemResponse] = Field(default_factory=list)


class GameStateResponse(BaseModel):
    settings: UserGameSettingsResponse
    today: DailyActivitySummaryResponse
    wallet: UserWalletResponse
    inventory: list[UserInventoryItemResponse] = Field(default_factory=list)
    stack_profiles: StackProfilesResponse
    stack_rewards: list[UserStackRewardResponse] = Field(default_factory=list)
    pending_packages: list[RewardPackageResponse] = Field(default_factory=list)


class RewardPackageCreateItem(BaseModel):
    item_type: RewardPackageItemType
    item_key: str
    quantity: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class RewardPackageCreate(BaseModel):
    user_id: int
    grant_id: int
    source: RewardPackageSource
    title: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    items: list[RewardPackageCreateItem]


class StackRewardUpsert(BaseModel):
    user_id: int
    reward_key: str
    reward_type: StackRewardType
    source_language: str
    stack_reward_level: int


def _to_stack_profile_response(profile: UserStackProfile) -> StackProfileResponse:
    return StackProfileResponse.model_validate(profile)


def _to_user_game_settings_response(settings: UserGameSettings) -> UserGameSettingsResponse:
    return UserGameSettingsResponse.model_validate(settings)


def _to_package_response(package: RewardPackage) -> RewardPackageResponse:
    return RewardPackageResponse(
        id=package.id,
        source=RewardPackageSource(package.source),
        status=RewardPackageStatus(package.status),
        title=package.title,
        description=package.description,
        created_at=package.created_at,
        claimed_at=package.claimed_at,
        metadata=package.package_metadata or {},
        items=[
            RewardPackageItemResponse(
                id=item.id,
                item_type=RewardPackageItemType(item.item_type),
                item_key=item.item_key,
                quantity=item.quantity,
                metadata=item.item_metadata or {},
            )
            for item in package.items
        ],
    )


def _to_stack_reward_response(stack_reward: UserStackReward) -> UserStackRewardResponse:
    return UserStackRewardResponse(
        reward_key=stack_reward.reward_key,
        reward_type=StackRewardType(stack_reward.reward_type),
        source_language=stack_reward.source_language,
        stage=stack_reward.stage,
        stack_reward_level=stack_reward.stack_reward_level,
        exp=stack_reward.exp,
        is_featured=stack_reward.is_featured,
        updated_at=stack_reward.updated_at,
    )


def _to_wallet_response(wallet: UserWallet) -> UserWalletResponse:
    return UserWalletResponse(coins=wallet.coins, updated_at=wallet.updated_at)


def _to_inventory_item_response(item: UserInventoryItem) -> UserInventoryItemResponse:
    return UserInventoryItemResponse(
        item_type=RewardPackageItemType(item.item_type),
        item_key=item.item_key,
        quantity=item.quantity,
        metadata=item.item_metadata or {},
        updated_at=item.updated_at,
    )


class GameRepository:
    async def get_or_create_user_settings(self, user_id: int) -> UserGameSettingsResponse:
        async with get_db() as db:
            result = await db.execute(
                select(UserGameSettings).where(UserGameSettings.user_id == user_id)
            )
            settings = result.scalar_one_or_none()
            if settings is None:
                settings = UserGameSettings(user_id=user_id, timezone=DEFAULT_USER_TIMEZONE)
                db.add(settings)
                await db.commit()
                await db.refresh(settings)
            return _to_user_game_settings_response(settings)

    async def update_user_settings(
        self,
        *,
        user_id: int,
        form: UserGameSettingsUpdate,
    ) -> UserGameSettingsResponse:
        async with get_db() as db:
            result = await db.execute(
                select(UserGameSettings).where(UserGameSettings.user_id == user_id)
            )
            settings = result.scalar_one_or_none()
            now = datetime.now(UTC)
            if settings is None:
                settings = UserGameSettings(
                    user_id=user_id,
                    timezone=form.timezone,
                    created_at=now,
                    updated_at=now,
                )
                db.add(settings)
            else:
                settings.timezone = form.timezone
                settings.updated_at = now
            await db.commit()
            await db.refresh(settings)
            return _to_user_game_settings_response(settings)

    async def list_daily_activity_counts(
        self,
        *,
        user_id: int,
        window_start: datetime,
        window_end: datetime,
    ) -> dict[ActivityType, int]:
        async with get_db() as db:
            result = await db.execute(
                select(Activity.type, func.count(Activity.id))
                .where(
                    Activity.user_id == user_id,
                    Activity.occurred_at >= window_start,
                    Activity.occurred_at < window_end,
                )
                .group_by(Activity.type)
            )
            return {
                ActivityType(activity_type): int(count) for activity_type, count in result.all()
            }

    async def upsert_stack_profiles(
        self,
        *,
        user_id: int,
        profiles: list[StackProfileUpsert],
    ) -> list[StackProfileResponse]:
        responses: list[StackProfileResponse] = []
        async with get_db() as db:
            languages = {profile.language for profile in profiles}
            for profile in profiles:
                result = await db.execute(
                    select(UserStackProfile).where(
                        UserStackProfile.user_id == profile.user_id,
                        UserStackProfile.language == profile.language,
                    )
                )
                existing = result.scalar_one_or_none()
                now = datetime.now(UTC)
                if existing is None:
                    existing = UserStackProfile(**profile.model_dump())
                    db.add(existing)
                    await db.flush()
                else:
                    existing.total_bytes = profile.total_bytes
                    existing.ratio = profile.ratio
                    existing.repository_count = profile.repository_count
                    existing.recent_activity_count = profile.recent_activity_count
                    existing.active_days_30d = profile.active_days_30d
                    existing.score = profile.score
                    existing.tier = profile.tier
                    existing.mastery_level = profile.mastery_level
                    existing.calculated_at = profile.calculated_at
                    existing.updated_at = now
                responses.append(_to_stack_profile_response(existing))
            stale_profiles = delete(UserStackProfile).where(UserStackProfile.user_id == user_id)
            if languages:
                stale_profiles = stale_profiles.where(UserStackProfile.language.not_in(languages))
            await db.execute(stale_profiles)
            await db.commit()
        return sorted(responses, key=lambda item: item.total_bytes, reverse=True)

    async def list_stack_profiles(self, user_id: int) -> StackProfilesResponse:
        async with get_db() as db:
            result = await db.execute(
                select(UserStackProfile)
                .where(UserStackProfile.user_id == user_id)
                .order_by(UserStackProfile.total_bytes.desc(), UserStackProfile.language)
            )
            return StackProfilesResponse(
                items=[_to_stack_profile_response(profile) for profile in result.scalars().all()]
            )

    async def create_grant_once(
        self,
        *,
        user_id: int,
        grant_key: str,
        source: RewardPackageSource,
    ) -> tuple[RewardGrant, bool]:
        async with get_db() as db:
            result = await db.execute(
                select(RewardGrant).where(
                    RewardGrant.user_id == user_id,
                    RewardGrant.grant_key == grant_key,
                )
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                return existing, False

            grant = RewardGrant(user_id=user_id, grant_key=grant_key, source=source.value)
            db.add(grant)
            try:
                await db.commit()
                await db.refresh(grant)
            except IntegrityError:
                await db.rollback()
                result = await db.execute(
                    select(RewardGrant).where(
                        RewardGrant.user_id == user_id,
                        RewardGrant.grant_key == grant_key,
                    )
                )
                existing = result.scalar_one()
                return existing, False
            return grant, True

    async def create_package_once(
        self,
        package: RewardPackageCreate,
    ) -> RewardPackageResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(RewardPackage)
                .options(selectinload(RewardPackage.items))
                .where(RewardPackage.grant_id == package.grant_id)
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                return None

            db_package = RewardPackage(
                user_id=package.user_id,
                grant_id=package.grant_id,
                source=package.source.value,
                title=package.title,
                description=package.description,
                package_metadata=package.metadata,
            )
            db.add(db_package)
            await db.flush()
            for item in package.items:
                db.add(
                    RewardPackageItem(
                        package_id=db_package.id,
                        item_type=item.item_type.value,
                        item_key=item.item_key,
                        quantity=item.quantity,
                        item_metadata=item.metadata,
                    )
                )
            await db.commit()
            result = await db.execute(
                select(RewardPackage)
                .options(selectinload(RewardPackage.items))
                .where(RewardPackage.id == db_package.id)
            )
            return _to_package_response(result.scalar_one())

    async def get_package_by_grant_id(self, grant_id: int) -> RewardPackageResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(RewardPackage)
                .options(selectinload(RewardPackage.items))
                .where(RewardPackage.grant_id == grant_id)
            )
            package = result.scalar_one_or_none()
            if package is None:
                return None
            return _to_package_response(package)

    async def list_reward_packages(
        self,
        user_id: int,
        status: RewardPackageStatus | None = None,
    ) -> list[RewardPackageResponse]:
        async with get_db() as db:
            query = (
                select(RewardPackage)
                .options(selectinload(RewardPackage.items))
                .where(RewardPackage.user_id == user_id)
                .order_by(RewardPackage.created_at.desc(), RewardPackage.id.desc())
            )
            if status is not None:
                query = query.where(RewardPackage.status == status.value)
            result = await db.execute(query)
            return [_to_package_response(package) for package in result.scalars().unique().all()]

    async def get_or_create_wallet(self, user_id: int) -> UserWalletResponse:
        async with get_db() as db:
            wallet = await self._get_or_create_wallet_in_session(db, user_id=user_id)
            await db.commit()
            await db.refresh(wallet)
            return _to_wallet_response(wallet)

    async def list_inventory_items(self, user_id: int) -> list[UserInventoryItemResponse]:
        async with get_db() as db:
            result = await db.execute(
                select(UserInventoryItem)
                .where(UserInventoryItem.user_id == user_id)
                .order_by(UserInventoryItem.item_type, UserInventoryItem.item_key)
            )
            return [_to_inventory_item_response(item) for item in result.scalars().all()]

    async def list_stack_rewards(self, user_id: int) -> list[UserStackRewardResponse]:
        async with get_db() as db:
            result = await db.execute(
                select(UserStackReward)
                .where(UserStackReward.user_id == user_id)
                .order_by(UserStackReward.source_language, UserStackReward.reward_key)
            )
            return [_to_stack_reward_response(reward) for reward in result.scalars().all()]

    async def claim_reward_package(
        self,
        *,
        user_id: int,
        package_id: int,
    ) -> RewardPackageClaimResponse:
        async with get_db() as db:
            result = await db.execute(
                select(RewardPackage)
                .options(selectinload(RewardPackage.items))
                .where(
                    RewardPackage.id == package_id,
                    RewardPackage.user_id == user_id,
                )
            )
            package = result.scalar_one_or_none()
            if package is None:
                raise GameException(code=GameErrorCode.REWARD_PACKAGE_NOT_FOUND)
            if package.status != RewardPackageStatus.PENDING.value:
                raise GameException(code=GameErrorCode.REWARD_PACKAGE_ALREADY_CLAIMED)

            stack_rewards: list[UserStackReward] = []
            inventory_items: list[UserInventoryItem] = []
            wallet: UserWallet | None = None
            for item in package.items:
                if (
                    item.item_type == RewardPackageItemType.CURRENCY.value
                    and item.item_key == "coins"
                ):
                    wallet = await self._get_or_create_wallet_in_session(db, user_id=user_id)
                    wallet.coins += item.quantity
                    wallet.updated_at = datetime.now(UTC)
                    continue
                if item.item_type in {
                    RewardPackageItemType.FOOD.value,
                    RewardPackageItemType.PET_EXP.value,
                    RewardPackageItemType.MATERIAL.value,
                    RewardPackageItemType.COSMETIC.value,
                }:
                    inventory_items.append(
                        await self._upsert_inventory_item_in_session(
                            db,
                            user_id=user_id,
                            item_type=RewardPackageItemType(item.item_type),
                            item_key=item.item_key,
                            quantity=item.quantity,
                            metadata=item.item_metadata or {},
                        )
                    )
                    continue
                if item.item_type != RewardPackageItemType.STACK_REWARD_UPGRADE.value:
                    continue

                metadata = item.item_metadata or {}
                reward_key = item.item_key
                reward_type = metadata.get("reward_type")
                language = metadata.get("language")
                level = metadata.get("mastery_level")
                if not isinstance(reward_type, str) or not isinstance(language, str):
                    continue
                if not isinstance(level, int):
                    continue
                stack_reward = await self._upsert_stack_reward_in_session(
                    db,
                    user_id=user_id,
                    reward_key=reward_key,
                    reward_type=StackRewardType(reward_type),
                    source_language=language,
                    stack_reward_level=level,
                )
                stack_rewards.append(stack_reward)

            now = datetime.now(UTC)
            package.status = RewardPackageStatus.CLAIMED.value
            package.claimed_at = now
            await db.commit()
            await db.refresh(package)
            if wallet is not None:
                await db.refresh(wallet)
            for inventory_item in inventory_items:
                await db.refresh(inventory_item)
            result = await db.execute(
                select(RewardPackage)
                .options(selectinload(RewardPackage.items))
                .where(RewardPackage.id == package_id)
            )
            claimed_package = result.scalar_one()
            return RewardPackageClaimResponse(
                package=_to_package_response(claimed_package),
                stack_rewards=[
                    _to_stack_reward_response(stack_reward) for stack_reward in stack_rewards
                ],
                wallet=_to_wallet_response(wallet) if wallet is not None else None,
                inventory=[
                    _to_inventory_item_response(inventory_item)
                    for inventory_item in inventory_items
                ],
            )

    async def _get_or_create_wallet_in_session(
        self,
        db: AsyncSession,
        /,
        *,
        user_id: int,
    ) -> UserWallet:
        result = await db.execute(select(UserWallet).where(UserWallet.user_id == user_id))
        wallet = result.scalar_one_or_none()
        if wallet is None:
            wallet = UserWallet(user_id=user_id, coins=0)
            db.add(wallet)
            await db.flush()
        return wallet

    async def _upsert_inventory_item_in_session(
        self,
        db: AsyncSession,
        /,
        *,
        user_id: int,
        item_type: RewardPackageItemType,
        item_key: str,
        quantity: int,
        metadata: dict[str, Any],
    ) -> UserInventoryItem:
        result = await db.execute(
            select(UserInventoryItem).where(
                UserInventoryItem.user_id == user_id,
                UserInventoryItem.item_type == item_type.value,
                UserInventoryItem.item_key == item_key,
            )
        )
        inventory_item = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if inventory_item is None:
            inventory_item = UserInventoryItem(
                user_id=user_id,
                item_type=item_type.value,
                item_key=item_key,
                quantity=quantity,
                item_metadata=metadata,
            )
            db.add(inventory_item)
            await db.flush()
        else:
            inventory_item.quantity += quantity
            inventory_item.item_metadata = metadata
            inventory_item.updated_at = now
        return inventory_item

    async def _upsert_stack_reward_in_session(
        self,
        db: AsyncSession,
        /,
        *,
        user_id: int,
        reward_key: str,
        reward_type: StackRewardType,
        source_language: str,
        stack_reward_level: int,
    ) -> UserStackReward:
        result = await db.execute(
            select(UserStackReward).where(
                UserStackReward.user_id == user_id,
                UserStackReward.reward_key == reward_key,
            )
        )
        stack_reward = result.scalar_one_or_none()
        stage = _resolve_reward_stage(reward_type, stack_reward_level)
        now = datetime.now(UTC)
        if stack_reward is None:
            stack_reward = UserStackReward(
                user_id=user_id,
                reward_key=reward_key,
                reward_type=reward_type.value,
                source_language=source_language,
                stage=stage,
                stack_reward_level=stack_reward_level,
            )
            db.add(stack_reward)
            await db.flush()
        else:
            stack_reward.stage = max(stack_reward.stage, stage)
            stack_reward.stack_reward_level = max(
                stack_reward.stack_reward_level,
                stack_reward_level,
            )
            stack_reward.updated_at = now
        return stack_reward


def _resolve_reward_stage(reward_type: StackRewardType, level: int) -> int:
    if reward_type == StackRewardType.ANIMAL:
        if level >= 4:
            return 3
        if level >= 3:
            return 2
        return 1
    if level >= 5:
        return 3
    if level >= 3:
        return 2
    return 1


GameData = GameRepository()
