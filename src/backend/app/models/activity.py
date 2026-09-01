from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base, get_db


class ActivityType(StrEnum):
    COMMIT = "COMMIT"
    PUSH = "PUSH"
    PULL_REQUEST_OPENED = "PULL_REQUEST_OPENED"
    PULL_REQUEST_MERGED = "PULL_REQUEST_MERGED"
    REVIEW = "REVIEW"
    ISSUE = "ISSUE"
    RELEASE = "RELEASE"


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(60), nullable=False, default="WEBHOOK", index=True)
    github_installation_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    repository_github_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    repository_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_delivery_id: Mapped[str | None] = mapped_column(
        String(128), unique=True, index=True, nullable=True
    )
    github_external_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    user = relationship("User")


class ActivityCreate(BaseModel):
    user_id: int
    type: ActivityType
    source: str = "WEBHOOK"
    github_installation_id: int | None = None
    repository_github_id: int | None = None
    repository_full_name: str | None = None
    github_delivery_id: str | None = None
    github_external_id: str | None = None
    occurred_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActivityResponse(BaseModel):
    id: int
    user_id: int
    type: ActivityType
    source: str = "WEBHOOK"
    github_installation_id: int | None = None
    repository_github_id: int | None = None
    repository_full_name: str | None = None
    github_delivery_id: str | None = None
    github_external_id: str | None = None
    occurred_at: datetime
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ActivityCreateResult(BaseModel):
    activity: ActivityResponse
    duplicate: bool = False


def _to_response(activity: Activity) -> ActivityResponse:
    return ActivityResponse(
        id=activity.id,
        user_id=activity.user_id,
        type=ActivityType(activity.type),
        source=activity.source,
        github_installation_id=activity.github_installation_id,
        repository_github_id=activity.repository_github_id,
        repository_full_name=activity.repository_full_name,
        github_delivery_id=activity.github_delivery_id,
        github_external_id=activity.github_external_id,
        occurred_at=activity.occurred_at,
        created_at=activity.created_at,
        metadata=activity.event_metadata or {},
    )


class ActivityRepository:
    async def create_activity_once(self, activity: ActivityCreate) -> ActivityCreateResult:
        async with get_db() as db:
            if activity.github_delivery_id:
                result = await db.execute(
                    select(Activity).where(
                        Activity.github_delivery_id == activity.github_delivery_id
                    )
                )
                existing = result.scalar_one_or_none()
                if existing is not None:
                    return ActivityCreateResult(activity=_to_response(existing), duplicate=True)
            if activity.github_external_id:
                result = await db.execute(
                    select(Activity).where(
                        Activity.github_external_id == activity.github_external_id
                    )
                )
                existing = result.scalar_one_or_none()
                if existing is not None:
                    return ActivityCreateResult(activity=_to_response(existing), duplicate=True)

            db_activity = Activity(
                user_id=activity.user_id,
                type=activity.type.value,
                source=activity.source,
                github_installation_id=activity.github_installation_id,
                repository_github_id=activity.repository_github_id,
                repository_full_name=activity.repository_full_name,
                github_delivery_id=activity.github_delivery_id,
                github_external_id=activity.github_external_id,
                occurred_at=activity.occurred_at,
                event_metadata=activity.metadata,
            )
            db.add(db_activity)
            try:
                await db.commit()
                await db.refresh(db_activity)
            except IntegrityError:
                await db.rollback()
                if activity.github_delivery_id:
                    result = await db.execute(
                        select(Activity).where(
                            Activity.github_delivery_id == activity.github_delivery_id
                        )
                    )
                    existing = result.scalar_one_or_none()
                    if existing is not None:
                        return ActivityCreateResult(
                            activity=_to_response(existing),
                            duplicate=True,
                        )
                if activity.github_external_id:
                    result = await db.execute(
                        select(Activity).where(
                            Activity.github_external_id == activity.github_external_id
                        )
                    )
                    existing = result.scalar_one_or_none()
                    if existing is not None:
                        return ActivityCreateResult(
                            activity=_to_response(existing),
                            duplicate=True,
                        )
                raise
            return ActivityCreateResult(activity=_to_response(db_activity), duplicate=False)

    async def list_user_activities(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[ActivityResponse]:
        async with get_db() as db:
            result = await db.execute(
                select(Activity)
                .where(Activity.user_id == user_id)
                .order_by(Activity.occurred_at.desc(), Activity.id.desc())
                .limit(limit)
            )
            return [_to_response(activity) for activity in result.scalars().all()]


Activities = ActivityRepository()
