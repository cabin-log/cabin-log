import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.core.db.session as database
from app.core.cache.redis import RedisManager
from app.core.config.settings import SETTINGS
from app.core.mail.service import MAIL_SERVICE, NullMailProvider
from app.models.user import AuthIdentity, Credential, User, UserResponse, UserRole
from app.utils.security import hash_password
from tests.fixtures.scenario_seed_data import (
    DEFAULT_SEED_PROFILE,
    SeedProfileSchema,
)


@pytest.fixture
def sample_user() -> UserResponse:
    return UserResponse(
        id=1,
        email="tester@example.com",
        name="Tester",
        role=UserRole.USER,
        profile_image_url=None,
        oauth_providers=[],
        is_verified=True,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_admin_user() -> UserResponse:
    return UserResponse(
        id=99,
        email="admin@example.com",
        name="Admin",
        role=UserRole.ADMIN,
        profile_image_url=None,
        oauth_providers=[],
        is_verified=True,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def integration_client(tmp_path: Path):
    """Integration harness with deterministic auth defaults (email disabled)."""
    original_database_url = SETTINGS.DATABASE_URL
    original_email_enabled = SETTINGS.EMAIL_ENABLED
    original_login_enabled = SETTINGS.LOGIN_ENABLED
    original_password_auth_enabled = SETTINGS.PASSWORD_AUTH_ENABLED
    original_provider = MAIL_SERVICE._provider
    test_db_url = f"sqlite+aiosqlite:///{(tmp_path / 'integration.db').as_posix()}"

    object.__setattr__(SETTINGS, "DATABASE_URL", test_db_url)
    object.__setattr__(SETTINGS, "LOGIN_ENABLED", True)
    object.__setattr__(SETTINGS, "PASSWORD_AUTH_ENABLED", True)
    object.__setattr__(SETTINGS, "EMAIL_ENABLED", False)
    object.__setattr__(MAIL_SERVICE, "_provider", NullMailProvider())

    database._ENGINE = None
    database._SESSION_FACTORY = None
    asyncio.run(RedisManager.close())

    from app.main import create_app

    app = create_app()
    try:
        with TestClient(app) as client:
            yield client
    finally:
        asyncio.run(RedisManager.close())
        object.__setattr__(SETTINGS, "DATABASE_URL", original_database_url)
        object.__setattr__(SETTINGS, "EMAIL_ENABLED", original_email_enabled)
        object.__setattr__(SETTINGS, "LOGIN_ENABLED", original_login_enabled)
        object.__setattr__(SETTINGS, "PASSWORD_AUTH_ENABLED", original_password_auth_enabled)
        object.__setattr__(MAIL_SERVICE, "_provider", original_provider)
        database._ENGINE = None
        database._SESSION_FACTORY = None


@pytest.fixture
def email_enabled_integration_client(tmp_path: Path):
    """Integration harness for EMAIL_ENABLED=true flow (provider mocked to null sender)."""
    original_database_url = SETTINGS.DATABASE_URL
    original_email_enabled = SETTINGS.EMAIL_ENABLED
    original_login_enabled = SETTINGS.LOGIN_ENABLED
    original_password_auth_enabled = SETTINGS.PASSWORD_AUTH_ENABLED
    original_provider = MAIL_SERVICE._provider
    test_db_url = f"sqlite+aiosqlite:///{(tmp_path / 'integration-email-enabled.db').as_posix()}"

    object.__setattr__(SETTINGS, "DATABASE_URL", test_db_url)
    object.__setattr__(SETTINGS, "LOGIN_ENABLED", True)
    object.__setattr__(SETTINGS, "PASSWORD_AUTH_ENABLED", True)
    object.__setattr__(SETTINGS, "EMAIL_ENABLED", True)
    object.__setattr__(MAIL_SERVICE, "_provider", NullMailProvider())

    database._ENGINE = None
    database._SESSION_FACTORY = None
    asyncio.run(RedisManager.close())

    from app.main import create_app

    app = create_app()
    try:
        with TestClient(app) as client:
            yield client
    finally:
        asyncio.run(RedisManager.close())
        object.__setattr__(SETTINGS, "DATABASE_URL", original_database_url)
        object.__setattr__(SETTINGS, "EMAIL_ENABLED", original_email_enabled)
        object.__setattr__(SETTINGS, "LOGIN_ENABLED", original_login_enabled)
        object.__setattr__(SETTINGS, "PASSWORD_AUTH_ENABLED", original_password_auth_enabled)
        object.__setattr__(MAIL_SERVICE, "_provider", original_provider)
        database._ENGINE = None
        database._SESSION_FACTORY = None


@pytest.fixture
def password_auth_disabled_integration_client(tmp_path: Path):
    """Integration harness that keeps login on but blocks email/password auth routes."""
    original_database_url = SETTINGS.DATABASE_URL
    original_email_enabled = SETTINGS.EMAIL_ENABLED
    original_login_enabled = SETTINGS.LOGIN_ENABLED
    original_password_auth_enabled = SETTINGS.PASSWORD_AUTH_ENABLED
    original_oauth_enabled = SETTINGS.OAUTH_ENABLED
    original_provider = MAIL_SERVICE._provider
    test_db_url = (
        f"sqlite+aiosqlite:///{(tmp_path / 'integration-password-disabled.db').as_posix()}"
    )

    object.__setattr__(SETTINGS, "DATABASE_URL", test_db_url)
    object.__setattr__(SETTINGS, "LOGIN_ENABLED", True)
    object.__setattr__(SETTINGS, "PASSWORD_AUTH_ENABLED", False)
    object.__setattr__(SETTINGS, "EMAIL_ENABLED", False)
    object.__setattr__(SETTINGS, "OAUTH_ENABLED", False)
    object.__setattr__(MAIL_SERVICE, "_provider", NullMailProvider())

    database._ENGINE = None
    database._SESSION_FACTORY = None
    asyncio.run(RedisManager.close())

    from app.main import create_app

    app = create_app()
    try:
        with TestClient(app) as client:
            yield client
    finally:
        asyncio.run(RedisManager.close())
        object.__setattr__(SETTINGS, "DATABASE_URL", original_database_url)
        object.__setattr__(SETTINGS, "EMAIL_ENABLED", original_email_enabled)
        object.__setattr__(SETTINGS, "LOGIN_ENABLED", original_login_enabled)
        object.__setattr__(SETTINGS, "PASSWORD_AUTH_ENABLED", original_password_auth_enabled)
        object.__setattr__(SETTINGS, "OAUTH_ENABLED", original_oauth_enabled)
        object.__setattr__(MAIL_SERVICE, "_provider", original_provider)
        database._ENGINE = None
        database._SESSION_FACTORY = None


async def _seed_default_users(
    *,
    seed_profile: SeedProfileSchema = DEFAULT_SEED_PROFILE,
) -> None:
    session_factory = database.get_session_factory()
    shared_password_hash = hash_password(seed_profile.primary_user.password)

    async with session_factory() as session:
        seed_users: list[User] = []

        primary_user = User(
            email=seed_profile.primary_user.email,
            name=seed_profile.primary_user.name,
            role=seed_profile.primary_user.role,
            is_verified=seed_profile.primary_user.is_verified,
        )
        primary_user.credential = Credential(password_hash=shared_password_hash)
        primary_user.auth_identities = [
            AuthIdentity(provider="email", identifier=seed_profile.primary_user.email)
        ]
        seed_users.append(primary_user)

        start_index = seed_profile.existing_user_start_index
        end_index = start_index + seed_profile.existing_user_count
        for index in range(start_index, end_index):
            email = f"{seed_profile.existing_user_email_prefix}-{index:02d}@example.com"
            user = User(
                email=email,
                name=f"{seed_profile.existing_user_name_prefix} {index:02d}",
                role=seed_profile.existing_user_role,
                is_verified=True,
            )
            user.credential = Credential(password_hash=shared_password_hash)
            user.auth_identities = [AuthIdentity(provider="email", identifier=email)]
            seed_users.append(user)

        session.add_all(seed_users)
        await session.commit()


@pytest.fixture
def seeded_integration_client(integration_client: TestClient):
    asyncio.run(_seed_default_users())
    yield integration_client
