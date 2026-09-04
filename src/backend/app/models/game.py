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


class CabinObjectType(StrEnum):
    SYSTEM = "SYSTEM"
    STACK_REWARD = "STACK_REWARD"
    INVENTORY_ITEM = "INVENTORY_ITEM"
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
DEFAULT_CABIN_WIDTH = 12
DEFAULT_CABIN_DEPTH = 12
DEFAULT_TILE_WIDTH = 60
DEFAULT_TILE_HEIGHT = 30
DEFAULT_TILE_Z_HEIGHT = 46
DEFAULT_DASHBOARD_OBJECT_KEY = "system.dev-board"


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


class Cabin(Base):
    __tablename__ = "cabins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    width: Mapped[int] = mapped_column(Integer, default=DEFAULT_CABIN_WIDTH, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=DEFAULT_CABIN_DEPTH, nullable=False)
    tile_width: Mapped[int] = mapped_column(Integer, default=DEFAULT_TILE_WIDTH, nullable=False)
    tile_height: Mapped[int] = mapped_column(Integer, default=DEFAULT_TILE_HEIGHT, nullable=False)
    tile_z_height: Mapped[int] = mapped_column(
        Integer, default=DEFAULT_TILE_Z_HEIGHT, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")
    placements = relationship(
        "CabinPlacement",
        back_populates="cabin",
        cascade="all, delete-orphan",
    )


class CabinPlacement(Base):
    __tablename__ = "cabin_placements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cabin_id: Mapped[int] = mapped_column(
        ForeignKey("cabins.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    object_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    object_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    z: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rotation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    cabin = relationship("Cabin", back_populates="placements")
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


class CabinPlacementBase(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    z: int = Field(default=0, ge=0, le=3)
    rotation: int = 0
    width: int = Field(default=1, ge=1, le=4)
    depth: int = Field(default=1, ge=1, le=4)

    @field_validator("rotation")
    @classmethod
    def validate_rotation(cls, value: int) -> int:
        if value not in {0, 90, 180, 270}:
            raise ValueError("rotation must be one of 0, 90, 180, or 270.")
        return value


class CabinPlacementCreate(CabinPlacementBase):
    object_type: CabinObjectType
    object_key: str = Field(min_length=1, max_length=255)


class CabinPlacementUpdate(BaseModel):
    x: int | None = Field(default=None, ge=0)
    y: int | None = Field(default=None, ge=0)
    z: int | None = Field(default=None, ge=0, le=3)
    rotation: int | None = None
    width: int | None = Field(default=None, ge=1, le=4)
    depth: int | None = Field(default=None, ge=1, le=4)

    @field_validator("rotation")
    @classmethod
    def validate_rotation(cls, value: int | None) -> int | None:
        if value is not None and value not in {0, 90, 180, 270}:
            raise ValueError("rotation must be one of 0, 90, 180, or 270.")
        return value


class CabinPlacementResponse(BaseModel):
    id: int
    object_type: CabinObjectType
    object_key: str
    x: int
    y: int
    z: int
    rotation: int
    width: int
    depth: int
    locked: bool = False
    updated_at: datetime


class CabinResponse(BaseModel):
    id: int
    width: int
    depth: int
    tile_width: int
    tile_height: int
    tile_z_height: int
    placements: list[CabinPlacementResponse] = Field(default_factory=list)
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
    cabin: CabinResponse
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


def _to_cabin_placement_response(placement: CabinPlacement) -> CabinPlacementResponse:
    return CabinPlacementResponse(
        id=placement.id,
        object_type=CabinObjectType(placement.object_type),
        object_key=placement.object_key,
        x=placement.x,
        y=placement.y,
        z=placement.z,
        rotation=placement.rotation,
        width=placement.width,
        depth=placement.depth,
        locked=placement.object_type == CabinObjectType.SYSTEM.value,
        updated_at=placement.updated_at,
    )


def _to_cabin_response(cabin: Cabin) -> CabinResponse:
    placements = sorted(cabin.placements, key=lambda item: (item.z, item.y, item.x, item.id))
    return CabinResponse(
        id=cabin.id,
        width=cabin.width,
        depth=cabin.depth,
        tile_width=cabin.tile_width,
        tile_height=cabin.tile_height,
        tile_z_height=cabin.tile_z_height,
        placements=[_to_cabin_placement_response(placement) for placement in placements],
        updated_at=cabin.updated_at,
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

    async def get_or_create_cabin(self, user_id: int) -> CabinResponse:
        async with get_db() as db:
            cabin = await self._get_or_create_cabin_in_session(db, user_id=user_id)
            cabin_id = cabin.id
            await db.commit()
            return await self._load_cabin_response(db, cabin_id=cabin_id, user_id=user_id)

    async def create_cabin_placement(
        self,
        *,
        user_id: int,
        form: CabinPlacementCreate,
    ) -> CabinPlacementResponse:
        async with get_db() as db:
            cabin = await self._get_or_create_cabin_in_session(db, user_id=user_id)
            await self._validate_placeable_object(db, user_id=user_id, form=form)
            self._validate_cabin_bounds(
                cabin=cabin,
                x=form.x,
                y=form.y,
                z=form.z,
                width=form.width,
                depth=form.depth,
            )
            await self._ensure_no_cabin_collision(
                db,
                cabin_id=cabin.id,
                x=form.x,
                y=form.y,
                z=form.z,
                width=form.width,
                depth=form.depth,
            )
            placement = CabinPlacement(
                cabin_id=cabin.id,
                user_id=user_id,
                object_type=form.object_type.value,
                object_key=form.object_key,
                x=form.x,
                y=form.y,
                z=form.z,
                rotation=form.rotation,
                width=form.width,
                depth=form.depth,
            )
            db.add(placement)
            await db.commit()
            await db.refresh(placement)
            return _to_cabin_placement_response(placement)

    async def update_cabin_placement(
        self,
        *,
        user_id: int,
        placement_id: int,
        form: CabinPlacementUpdate,
    ) -> CabinPlacementResponse:
        async with get_db() as db:
            cabin = await self._get_or_create_cabin_in_session(db, user_id=user_id)
            result = await db.execute(
                select(CabinPlacement).where(
                    CabinPlacement.id == placement_id,
                    CabinPlacement.cabin_id == cabin.id,
                    CabinPlacement.user_id == user_id,
                )
            )
            placement = result.scalar_one_or_none()
            if placement is None:
                raise GameException(code=GameErrorCode.CABIN_PLACEMENT_NOT_FOUND)
            if placement.object_type == CabinObjectType.SYSTEM.value:
                raise GameException(code=GameErrorCode.CABIN_SYSTEM_PLACEMENT_LOCKED)

            x = placement.x if form.x is None else form.x
            y = placement.y if form.y is None else form.y
            z = placement.z if form.z is None else form.z
            rotation = placement.rotation if form.rotation is None else form.rotation
            width = placement.width if form.width is None else form.width
            depth = placement.depth if form.depth is None else form.depth
            self._validate_cabin_bounds(
                cabin=cabin,
                x=x,
                y=y,
                z=z,
                width=width,
                depth=depth,
            )
            await self._ensure_no_cabin_collision(
                db,
                cabin_id=cabin.id,
                x=x,
                y=y,
                z=z,
                width=width,
                depth=depth,
                exclude_placement_id=placement.id,
            )

            now = datetime.now(UTC)
            placement.x = x
            placement.y = y
            placement.z = z
            placement.rotation = rotation
            placement.width = width
            placement.depth = depth
            placement.updated_at = now
            cabin.updated_at = now
            await db.commit()
            await db.refresh(placement)
            return _to_cabin_placement_response(placement)

    async def delete_cabin_placement(self, *, user_id: int, placement_id: int) -> None:
        async with get_db() as db:
            cabin = await self._get_or_create_cabin_in_session(db, user_id=user_id)
            result = await db.execute(
                select(CabinPlacement).where(
                    CabinPlacement.id == placement_id,
                    CabinPlacement.cabin_id == cabin.id,
                    CabinPlacement.user_id == user_id,
                )
            )
            placement = result.scalar_one_or_none()
            if placement is None:
                raise GameException(code=GameErrorCode.CABIN_PLACEMENT_NOT_FOUND)
            if placement.object_type == CabinObjectType.SYSTEM.value:
                raise GameException(code=GameErrorCode.CABIN_SYSTEM_PLACEMENT_LOCKED)
            await db.delete(placement)
            cabin.updated_at = datetime.now(UTC)
            await db.commit()

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

    async def _get_or_create_cabin_in_session(
        self,
        db: AsyncSession,
        /,
        *,
        user_id: int,
    ) -> Cabin:
        result = await db.execute(select(Cabin).where(Cabin.user_id == user_id))
        cabin = result.scalar_one_or_none()
        if cabin is None:
            cabin = Cabin(user_id=user_id)
            db.add(cabin)
            await db.flush()
            db.add(
                CabinPlacement(
                    cabin_id=cabin.id,
                    user_id=user_id,
                    object_type=CabinObjectType.SYSTEM.value,
                    object_key=DEFAULT_DASHBOARD_OBJECT_KEY,
                    x=0,
                    y=0,
                    z=1,
                    rotation=0,
                    width=2,
                    depth=1,
                )
            )
            await db.flush()
        else:
            self._sync_cabin_grid_contract(cabin)
        return cabin

    def _sync_cabin_grid_contract(self, cabin: Cabin) -> None:
        cabin.width = DEFAULT_CABIN_WIDTH
        cabin.depth = DEFAULT_CABIN_DEPTH
        cabin.tile_width = DEFAULT_TILE_WIDTH
        cabin.tile_height = DEFAULT_TILE_HEIGHT
        cabin.tile_z_height = DEFAULT_TILE_Z_HEIGHT

    async def _load_cabin_response(
        self,
        db: AsyncSession,
        /,
        *,
        cabin_id: int,
        user_id: int,
    ) -> CabinResponse:
        result = await db.execute(
            select(Cabin)
            .options(selectinload(Cabin.placements))
            .where(Cabin.id == cabin_id, Cabin.user_id == user_id)
        )
        return _to_cabin_response(result.scalar_one())

    async def _validate_placeable_object(
        self,
        db: AsyncSession,
        /,
        *,
        user_id: int,
        form: CabinPlacementCreate,
    ) -> None:
        if form.object_type == CabinObjectType.SYSTEM:
            raise GameException(code=GameErrorCode.CABIN_SYSTEM_PLACEMENT_LOCKED)
        if form.object_type == CabinObjectType.STACK_REWARD:
            result = await db.execute(
                select(UserStackReward.id).where(
                    UserStackReward.user_id == user_id,
                    UserStackReward.reward_key == form.object_key,
                )
            )
            if result.scalar_one_or_none() is None:
                raise GameException(code=GameErrorCode.CABIN_ITEM_NOT_OWNED)
            return
        result = await db.execute(
            select(UserInventoryItem.id).where(
                UserInventoryItem.user_id == user_id,
                UserInventoryItem.item_key == form.object_key,
                UserInventoryItem.quantity > 0,
            )
        )
        if result.scalar_one_or_none() is None:
            raise GameException(code=GameErrorCode.CABIN_ITEM_NOT_OWNED)

    def _validate_cabin_bounds(
        self,
        *,
        cabin: Cabin,
        x: int,
        y: int,
        z: int,
        width: int,
        depth: int,
    ) -> None:
        if x + width > cabin.width or y + depth > cabin.depth or z > 3:
            raise GameException(
                code=GameErrorCode.CABIN_PLACEMENT_INVALID,
                details={
                    "cabin_width": cabin.width,
                    "cabin_depth": cabin.depth,
                    "max_z": 3,
                },
            )

    async def _ensure_no_cabin_collision(
        self,
        db: AsyncSession,
        /,
        *,
        cabin_id: int,
        x: int,
        y: int,
        z: int,
        width: int,
        depth: int,
        exclude_placement_id: int | None = None,
    ) -> None:
        result = await db.execute(
            select(CabinPlacement).where(
                CabinPlacement.cabin_id == cabin_id,
                CabinPlacement.z == z,
            )
        )
        for placement in result.scalars().all():
            if exclude_placement_id is not None and placement.id == exclude_placement_id:
                continue
            if _footprints_overlap(
                left_x=x,
                left_y=y,
                left_width=width,
                left_depth=depth,
                right_x=placement.x,
                right_y=placement.y,
                right_width=placement.width,
                right_depth=placement.depth,
            ):
                raise GameException(
                    code=GameErrorCode.CABIN_PLACEMENT_CONFLICT,
                    details={"conflicting_placement_id": placement.id},
                )


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


def _footprints_overlap(
    *,
    left_x: int,
    left_y: int,
    left_width: int,
    left_depth: int,
    right_x: int,
    right_y: int,
    right_width: int,
    right_depth: int,
) -> bool:
    return (
        left_x < right_x + right_width
        and left_x + left_width > right_x
        and left_y < right_y + right_depth
        and left_y + left_depth > right_y
    )


GameData = GameRepository()
