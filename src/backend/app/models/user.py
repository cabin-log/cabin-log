from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from app.core.db.session import Base, get_db
from app.core.error import AuthErrorCode, AuthException

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value, nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    credential = relationship(
        "Credential", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    auth_identities = relationship(
        "AuthIdentity", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User", back_populates="credential")


class AuthIdentity(Base):
    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "identifier", name="uq_auth_identities_provider_identifier"),
        UniqueConstraint("user_id", "provider", name="uq_auth_identities_user_provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="email", nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_login_user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user = relationship("User", back_populates="auth_identities")


class SignupForm(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    name: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=24)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one number.")
        if not any(not char.isalnum() for char in value):
            raise ValueError("Password must include at least one symbol.")
        if any(char.isspace() for char in value):
            raise ValueError("Password cannot contain spaces.")
        return value


class LoginForm(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    password: str = Field(min_length=8, max_length=24)
    remember_me: bool = False


class UpdateProfileForm(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    profile_image_url: str | None = Field(default=None, max_length=12_000_000)

    @field_validator("profile_image_url")
    @classmethod
    def validate_profile_image_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None

        allowed_data_url_prefixes = (
            "data:image/png;base64,",
            "data:image/jpeg;base64,",
            "data:image/jpg;base64,",
            "data:image/webp;base64,",
            "data:image/gif;base64,",
        )
        if normalized.startswith(("http://", "https://")):
            return normalized
        if normalized.startswith(allowed_data_url_prefixes):
            return normalized

        raise ValueError("profile_image_url must be a valid image URL or image data URL.")

    @model_validator(mode="after")
    def validate_fields(self):
        has_name = "name" in self.model_fields_set
        has_profile_image_url = "profile_image_url" in self.model_fields_set
        if not has_name and not has_profile_image_url:
            raise ValueError("At least one field must be provided.")
        if has_name and self.name is None:
            raise ValueError("name cannot be null.")
        return self


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    profile_image_url: str | None = None
    oauth_providers: list[str] = Field(default_factory=list)
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRoleStatsResponse(BaseModel):
    total_users: int
    active_users: int
    admin_users: int


class VerifyEmailForm(BaseModel):
    token: str = Field(min_length=16, max_length=512)


class VerifyEmailResponse(BaseModel):
    message: str
    user: UserResponse


class ResendVerificationForm(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)


class ResendVerificationResponse(BaseModel):
    message: str


class ForgotPasswordForm(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordForm(BaseModel):
    token: str = Field(min_length=16, max_length=512)
    password: str = Field(min_length=8, max_length=24)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one number.")
        if not any(not char.isalnum() for char in value):
            raise ValueError("Password must include at least one symbol.")
        if any(char.isspace() for char in value):
            raise ValueError("Password cannot contain spaces.")
        return value


class ResetPasswordResponse(BaseModel):
    message: str


class APIError(BaseModel):
    error: str
    message: str
    details: dict | None = None


class AuthUserDTO(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    profile_image_url: str | None = None
    oauth_providers: list[str] = Field(default_factory=list)
    is_active: bool
    is_verified: bool
    created_at: datetime
    password_hash: str | None = None

    def as_user_response(self) -> UserResponse:
        return UserResponse(
            id=self.id,
            email=self.email,
            name=self.name,
            role=self.role,
            profile_image_url=self.profile_image_url,
            oauth_providers=self.oauth_providers,
            is_verified=self.is_verified,
            created_at=self.created_at,
        )


def _extract_connected_oauth_providers(auth_identities: list[AuthIdentity] | None) -> list[str]:
    if not auth_identities:
        return []

    connected = {
        identity.provider.strip().lower()
        for identity in auth_identities
        if identity.provider and identity.provider.strip().lower() != "email"
    }
    return sorted(connected)


class UserRepository:
    async def create_signup_user(
        self,
        email: str,
        name: str,
        password_hash: str,
        is_verified: bool = False,
        role: UserRole = UserRole.USER,
    ) -> UserResponse:
        async with get_db() as db:
            existing = await db.execute(select(User.id).where(User.email == email).limit(1))
            if existing.first() is not None:
                raise AuthException(code=AuthErrorCode.EMAIL_ALREADY_EXISTS)

            user = User(email=email, name=name, role=role.value, is_verified=is_verified)
            user.credential = Credential(password_hash=password_hash)
            user.auth_identities = [AuthIdentity(provider="email", identifier=email)]
            db.add(user)

            try:
                await db.commit()
                await db.refresh(user)
            except IntegrityError:
                await db.rollback()
                raise

            return UserResponse.model_validate(user)

    async def create_oauth_user(
        self,
        email: str,
        name: str,
        provider: str,
        identifier: str,
        is_verified: bool = True,
        role: UserRole = UserRole.USER,
        profile_image_url: str | None = None,
    ) -> UserResponse:
        async with get_db() as db:
            existing = await db.execute(select(User.id).where(User.email == email).limit(1))
            if existing.first() is not None:
                raise AuthException(code=AuthErrorCode.EMAIL_ALREADY_EXISTS)

            user = User(
                email=email,
                name=name,
                role=role.value,
                profile_image_url=profile_image_url,
                is_verified=is_verified,
            )
            user.auth_identities = [AuthIdentity(provider=provider, identifier=identifier)]
            db.add(user)

            try:
                await db.commit()
                await db.refresh(user)
            except IntegrityError:
                await db.rollback()
                raise

            return UserResponse.model_validate(user)

    async def update_profile_image_url_if_empty(
        self, user_id: int, profile_image_url: str
    ) -> AuthUserDTO | None:
        async with get_db() as db:
            result = await db.execute(
                select(User).where(User.id == user_id, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None
            if user.profile_image_url:
                return None

            user.profile_image_url = profile_image_url
            user.updated_at = datetime.now(UTC)
            await db.commit()

        return await self.get_auth_user_by_id(user_id)

    async def get_auth_user_by_identity(self, provider: str, identifier: str) -> AuthUserDTO | None:
        async with get_db() as db:
            result = await db.execute(
                select(User)
                .join(AuthIdentity, AuthIdentity.user_id == User.id)
                .options(selectinload(User.credential), selectinload(User.auth_identities))
                .where(
                    AuthIdentity.provider == provider,
                    AuthIdentity.identifier == identifier,
                    User.is_active.is_(True),
                )
            )
            user = result.scalar_one_or_none()

        if user is None:
            return None

        return AuthUserDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            role=UserRole(user.role),
            profile_image_url=user.profile_image_url,
            oauth_providers=_extract_connected_oauth_providers(user.auth_identities),
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            password_hash=user.credential.password_hash if user.credential else None,
        )

    async def get_auth_user_by_email(self, email: str) -> AuthUserDTO | None:
        return await self.get_auth_user_by_identity(provider="email", identifier=email)

    async def get_user_response_by_email(self, email: str) -> UserResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(User).where(User.email == email, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None
            return UserResponse.model_validate(user)

    async def get_auth_user_by_id(self, user_id: int) -> AuthUserDTO | None:
        async with get_db() as db:
            result = await db.execute(
                select(User)
                .options(selectinload(User.credential), selectinload(User.auth_identities))
                .where(User.id == user_id, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()

        if user is None:
            return None

        return AuthUserDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            role=UserRole(user.role),
            profile_image_url=user.profile_image_url,
            oauth_providers=_extract_connected_oauth_providers(user.auth_identities),
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            password_hash=user.credential.password_hash if user.credential else None,
        )

    async def get_user_response_by_id(self, user_id: int) -> UserResponse | None:
        auth_user = await self.get_auth_user_by_id(user_id)
        if auth_user is None:
            return None
        return auth_user.as_user_response()

    async def link_auth_identity(self, user_id: int, provider: str, identifier: str) -> bool:
        async with get_db() as db:
            auth_identity = AuthIdentity(
                user_id=user_id,
                provider=provider,
                identifier=identifier,
            )
            db.add(auth_identity)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                return False
        return True

    async def update_login_metadata(
        self,
        user_id: int,
        provider: str,
        identifier: str,
        login_ip: str | None,
        user_agent: str | None,
        login_time: datetime,
    ) -> None:
        async with get_db() as db:
            result = await db.execute(
                select(AuthIdentity).where(
                    AuthIdentity.user_id == user_id,
                    AuthIdentity.provider == provider,
                    AuthIdentity.identifier == identifier,
                )
            )
            auth_identity = result.scalar_one_or_none()
            if auth_identity is None:
                return

            auth_identity.last_login_at = login_time
            auth_identity.last_login_ip = login_ip
            auth_identity.last_login_user_agent = user_agent
            await db.commit()

    async def mark_email_verified(self, user_id: int) -> UserResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(User).where(User.id == user_id, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None

            user.is_verified = True
            await db.commit()
            await db.refresh(user)
            return UserResponse.model_validate(user)

    async def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        async with get_db() as db:
            result = await db.execute(
                select(Credential)
                .join(User, User.id == Credential.user_id)
                .where(User.id == user_id, User.is_active.is_(True))
            )
            credential = result.scalar_one_or_none()
            if credential is None:
                return False

            credential.password_hash = password_hash
            credential.updated_at = datetime.now(UTC)
            await db.commit()
            return True

    async def update_user_profile(
        self,
        user_id: int,
        *,
        name: str | None,
        profile_image_url: str | None,
        update_name: bool,
        update_profile_image_url: bool,
    ) -> UserResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(User).where(User.id == user_id, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None

            if update_name and name is not None:
                user.name = name
            if update_profile_image_url:
                user.profile_image_url = profile_image_url
            user.updated_at = datetime.now(UTC)
            await db.commit()
        return await self.get_user_response_by_id(user_id)

    async def update_user_role(self, user_id: int, role: UserRole) -> UserResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(User).where(User.id == user_id, User.is_active.is_(True))
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None

            user.role = role.value
            user.updated_at = datetime.now(UTC)
            await db.commit()

        return await self.get_user_response_by_id(user_id)

    async def get_user_role_stats(self) -> dict[str, int]:
        async with get_db() as db:
            total_users = await db.scalar(select(func.count(User.id)))
            active_users = await db.scalar(
                select(func.count(User.id)).where(User.is_active.is_(True))
            )
            admin_users = await db.scalar(
                select(func.count(User.id)).where(User.role == UserRole.ADMIN.value)
            )

        return {
            "total_users": int(total_users or 0),
            "active_users": int(active_users or 0),
            "admin_users": int(admin_users or 0),
        }


Users = UserRepository()
