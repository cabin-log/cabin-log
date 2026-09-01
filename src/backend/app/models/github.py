from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    delete,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base, get_db


class GitHubProfile(Base):
    __tablename__ = "github_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    github_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    login: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")


class GitHubRepository(Base):
    __tablename__ = "github_repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_installation_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    github_repo_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    owner_login: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")
    languages = relationship(
        "GitHubRepositoryLanguage",
        back_populates="repository",
        cascade="all, delete-orphan",
    )


class GitHubRepositoryLanguage(Base):
    __tablename__ = "github_repository_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("github_repositories.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    repository = relationship("GitHubRepository", back_populates="languages")


class GitHubInstallation(Base):
    __tablename__ = "github_installations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    github_installation_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    account_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    account_login: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    target_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    repository_selection: Mapped[str | None] = mapped_column(String(60), nullable=True)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User")


class GitHubProfileUpsert(BaseModel):
    user_id: int
    github_user_id: int
    login: str
    display_name: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None


class GitHubProfileResponse(BaseModel):
    user_id: int
    github_user_id: int
    login: str
    display_name: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


class GitHubRepositoryUpsert(BaseModel):
    user_id: int
    github_installation_id: int | None = None
    github_repo_id: int
    owner_login: str
    name: str
    full_name: str
    private: bool = False
    html_url: str | None = None
    default_branch: str | None = None
    primary_language: str | None = None
    pushed_at: datetime | None = None
    languages: dict[str, int] = Field(default_factory=dict)


class GitHubRepositoryResponse(BaseModel):
    github_installation_id: int | None = None
    github_repo_id: int
    owner_login: str
    name: str
    full_name: str
    private: bool
    html_url: str | None = None
    default_branch: str | None = None
    primary_language: str | None = None
    pushed_at: datetime | None = None
    languages: dict[str, int] = Field(default_factory=dict)
    updated_at: datetime


class GitHubStackLanguageResponse(BaseModel):
    language: str
    bytes: int
    ratio: float


class GitHubStackSummaryResponse(BaseModel):
    total_bytes: int
    languages: list[GitHubStackLanguageResponse]


class GitHubAppInstallUrlResponse(BaseModel):
    configured: bool
    install_url: str | None = None


class GitHubInstallationSyncResponse(BaseModel):
    github_installation_id: int
    repository_count: int
    repositories: list[GitHubRepositoryResponse] = Field(default_factory=list)


class GitHubOAuthSyncResponse(BaseModel):
    repository_count: int
    created_activity_count: int
    duplicate_activity_count: int


class GitHubInstallationUpsert(BaseModel):
    user_id: int | None = None
    github_installation_id: int
    account_id: int | None = None
    account_login: str | None = None
    account_type: str | None = None
    target_type: str | None = None
    repository_selection: str | None = None
    suspended_at: datetime | None = None
    deleted_at: datetime | None = None


class GitHubInstallationResponse(BaseModel):
    user_id: int | None = None
    github_installation_id: int
    account_id: int | None = None
    account_login: str | None = None
    account_type: str | None = None
    target_type: str | None = None
    repository_selection: str | None = None
    suspended_at: datetime | None = None
    deleted_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


class GitHubProfileRepository:
    async def upsert_profile(self, profile: GitHubProfileUpsert) -> GitHubProfileResponse:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubProfile).where(GitHubProfile.user_id == profile.user_id)
            )
            existing = result.scalar_one_or_none()
            now = datetime.now(UTC)

            if existing is None:
                existing = GitHubProfile(**profile.model_dump())
                db.add(existing)
            else:
                existing.github_user_id = profile.github_user_id
                existing.login = profile.login
                existing.display_name = profile.display_name
                existing.avatar_url = profile.avatar_url
                existing.profile_url = profile.profile_url
                existing.updated_at = now

            try:
                await db.commit()
                await db.refresh(existing)
            except IntegrityError:
                await db.rollback()
                raise

            return GitHubProfileResponse.model_validate(existing)

    async def get_profile_by_user_id(self, user_id: int) -> GitHubProfileResponse | None:
        async with get_db() as db:
            result = await db.execute(select(GitHubProfile).where(GitHubProfile.user_id == user_id))
            profile = result.scalar_one_or_none()
            if profile is None:
                return None
            return GitHubProfileResponse.model_validate(profile)

    async def get_user_id_by_github_user_id(self, github_user_id: int) -> int | None:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubProfile.user_id).where(GitHubProfile.github_user_id == github_user_id)
            )
            return result.scalar_one_or_none()

    async def upsert_installation(
        self,
        installation: GitHubInstallationUpsert,
    ) -> GitHubInstallationResponse:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubInstallation).where(
                    GitHubInstallation.github_installation_id == installation.github_installation_id
                )
            )
            existing = result.scalar_one_or_none()
            now = datetime.now(UTC)
            if existing is None:
                existing = GitHubInstallation(**installation.model_dump())
                db.add(existing)
            else:
                if installation.user_id is not None:
                    existing.user_id = installation.user_id
                existing.account_id = installation.account_id
                existing.account_login = installation.account_login
                existing.account_type = installation.account_type
                existing.target_type = installation.target_type
                existing.repository_selection = installation.repository_selection
                existing.suspended_at = installation.suspended_at
                existing.deleted_at = installation.deleted_at
                existing.updated_at = now

            await db.commit()
            await db.refresh(existing)
            return GitHubInstallationResponse.model_validate(existing)

    async def get_installation_by_github_id(
        self,
        github_installation_id: int,
    ) -> GitHubInstallationResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubInstallation).where(
                    GitHubInstallation.github_installation_id == github_installation_id
                )
            )
            installation = result.scalar_one_or_none()
            if installation is None:
                return None
            return GitHubInstallationResponse.model_validate(installation)

    async def list_installations(self, user_id: int) -> list[GitHubInstallationResponse]:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubInstallation)
                .where(GitHubInstallation.user_id == user_id)
                .order_by(GitHubInstallation.updated_at.desc(), GitHubInstallation.id.desc())
            )
            return [
                GitHubInstallationResponse.model_validate(installation)
                for installation in result.scalars().all()
            ]

    async def mark_installation_deleted(self, github_installation_id: int) -> bool:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubInstallation).where(
                    GitHubInstallation.github_installation_id == github_installation_id
                )
            )
            installation = result.scalar_one_or_none()
            if installation is None:
                return False
            now = datetime.now(UTC)
            installation.deleted_at = now
            installation.updated_at = now
            await db.commit()
            return True

    async def upsert_repositories(
        self,
        repositories: list[GitHubRepositoryUpsert],
    ) -> list[GitHubRepositoryResponse]:
        responses: list[GitHubRepositoryResponse] = []
        async with get_db() as db:
            for repository in repositories:
                result = await db.execute(
                    select(GitHubRepository).where(
                        GitHubRepository.github_repo_id == repository.github_repo_id
                    )
                )
                existing = result.scalar_one_or_none()
                now = datetime.now(UTC)
                if existing is None:
                    existing = GitHubRepository(
                        user_id=repository.user_id,
                        github_installation_id=repository.github_installation_id,
                        github_repo_id=repository.github_repo_id,
                        owner_login=repository.owner_login,
                        name=repository.name,
                        full_name=repository.full_name,
                        private=repository.private,
                        html_url=repository.html_url,
                        default_branch=repository.default_branch,
                        primary_language=repository.primary_language,
                        pushed_at=repository.pushed_at,
                    )
                    db.add(existing)
                    await db.flush()
                else:
                    existing.user_id = repository.user_id
                    existing.github_installation_id = repository.github_installation_id
                    existing.owner_login = repository.owner_login
                    existing.name = repository.name
                    existing.full_name = repository.full_name
                    existing.private = repository.private
                    existing.html_url = repository.html_url
                    existing.default_branch = repository.default_branch
                    existing.primary_language = repository.primary_language
                    existing.pushed_at = repository.pushed_at
                    existing.updated_at = now
                    await db.execute(
                        delete(GitHubRepositoryLanguage).where(
                            GitHubRepositoryLanguage.repository_id == existing.id
                        )
                    )

                for language, byte_count in repository.languages.items():
                    if byte_count <= 0:
                        continue
                    db.add(
                        GitHubRepositoryLanguage(
                            repository_id=existing.id,
                            language=language,
                            bytes=byte_count,
                        )
                    )
                responses.append(_to_repository_response(existing, repository.languages))

            await db.commit()
        return responses

    async def list_repositories(self, user_id: int) -> list[GitHubRepositoryResponse]:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubRepository)
                .where(GitHubRepository.user_id == user_id)
                .order_by(GitHubRepository.pushed_at.desc().nullslast(), GitHubRepository.full_name)
            )
            repositories = result.scalars().unique().all()
            responses = []
            for repository in repositories:
                languages = await self._get_repository_languages(repository.id)
                responses.append(_to_repository_response(repository, languages))
            return responses

    async def remove_installation_repositories(
        self,
        *,
        github_installation_id: int,
        github_repo_ids: list[int],
    ) -> None:
        if not github_repo_ids:
            return
        async with get_db() as db:
            await db.execute(
                delete(GitHubRepository).where(
                    GitHubRepository.github_installation_id == github_installation_id,
                    GitHubRepository.github_repo_id.in_(github_repo_ids),
                )
            )
            await db.commit()

    async def get_stack_summary(self, user_id: int) -> GitHubStackSummaryResponse:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubRepositoryLanguage.language, GitHubRepositoryLanguage.bytes)
                .join(
                    GitHubRepository, GitHubRepository.id == GitHubRepositoryLanguage.repository_id
                )
                .where(GitHubRepository.user_id == user_id)
            )
            totals: dict[str, int] = {}
            for language, byte_count in result.all():
                totals[language] = totals.get(language, 0) + int(byte_count)

        total_bytes = sum(totals.values())
        languages = [
            GitHubStackLanguageResponse(
                language=language,
                bytes=bytes_count,
                ratio=(bytes_count / total_bytes) if total_bytes else 0,
            )
            for language, bytes_count in sorted(
                totals.items(), key=lambda item: item[1], reverse=True
            )
        ]
        return GitHubStackSummaryResponse(total_bytes=total_bytes, languages=languages)

    async def _get_repository_languages(self, repository_id: int) -> dict[str, int]:
        async with get_db() as db:
            result = await db.execute(
                select(GitHubRepositoryLanguage).where(
                    GitHubRepositoryLanguage.repository_id == repository_id
                )
            )
            return {language.language: language.bytes for language in result.scalars().all()}


def _to_repository_response(
    repository: GitHubRepository,
    languages: dict[str, int],
) -> GitHubRepositoryResponse:
    return GitHubRepositoryResponse(
        github_repo_id=repository.github_repo_id,
        github_installation_id=repository.github_installation_id,
        owner_login=repository.owner_login,
        name=repository.name,
        full_name=repository.full_name,
        private=repository.private,
        html_url=repository.html_url,
        default_branch=repository.default_branch,
        primary_language=repository.primary_language,
        pushed_at=repository.pushed_at,
        languages=languages,
        updated_at=repository.updated_at,
    )


GitHubProfiles = GitHubProfileRepository()
