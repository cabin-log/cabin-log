import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    # Agent customization note:
    # Add project-wide toggles here first. Keep env names stable for scripts.
    ROOT_DIR: Path = Path(__file__).resolve().parents[2]

    APP_NAME: str = os.getenv("APP_NAME", "Blueprint4FastAPI API")
    APP_ENV: str = os.getenv("APP_ENV", "local")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:5173")
    SWAGGER_ENABLED: bool = os.getenv("SWAGGER_ENABLED", "true").lower() == "true"
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    TRUST_PROXY_HEADERS: bool = os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"
    TRACING_ENABLED: bool = os.getenv("TRACING_ENABLED", "false").lower() == "true"
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "blueprint4fastapi-backend")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4317",
    )
    OTEL_EXPORTER_OTLP_INSECURE: bool = (
        os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true"
    )
    OTEL_EXPORTER_OTLP_TIMEOUT_SECONDS: int = int(
        os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT_SECONDS", "10")
    )
    OTEL_TRACE_SAMPLE_RATIO: float = float(os.getenv("OTEL_TRACE_SAMPLE_RATIO", "1.0"))

    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES", "60")
    )
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30")
    )
    LOGIN_FAILED_LIMIT: int = int(os.getenv("LOGIN_FAILED_LIMIT", "5"))
    LOGIN_LOCKED_MINUTES: int = int(os.getenv("LOGIN_LOCKED_MINUTES", "5"))
    LOGIN_ENABLED: bool = os.getenv("LOGIN_ENABLED", "true").lower() == "true"
    PASSWORD_AUTH_ENABLED: bool = os.getenv("PASSWORD_AUTH_ENABLED", "false").lower() == "true"
    BOOTSTRAP_USER_EMAIL: str = os.getenv("BOOTSTRAP_USER_EMAIL", "demo@example.com")
    BOOTSTRAP_USER_NAME: str = os.getenv("BOOTSTRAP_USER_NAME", "Demo User")

    DB_DRIVER: str = os.getenv("DB_DRIVER", "sqlite+aiosqlite")
    DB_NAME: str = os.getenv("DB_NAME", "template.db")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DATABASE_URL: str | None = None

    REDIS_IN_MEMORY: bool = os.getenv("REDIS_IN_MEMORY", "true").lower() == "true"
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD")
    REDIS_URL: str | None = None

    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "no-reply@example.com")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", os.getenv("SMTP_USER", ""))
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_STARTTLS: bool = os.getenv("SMTP_USE_STARTTLS", "true").lower() == "true"
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    SMTP_TIMEOUT_SECONDS: int = int(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    SMTP_VALIDATE_ON_STARTUP: bool = os.getenv("SMTP_VALIDATE_ON_STARTUP", "true").lower() == "true"
    EMAIL_BRAND_NAME: str = os.getenv("EMAIL_BRAND_NAME", "Blueprint4FastAPI")
    EMAIL_QUEUE_BLOCK_TIMEOUT_SECONDS: int = int(
        os.getenv("EMAIL_QUEUE_BLOCK_TIMEOUT_SECONDS", "2")
    )
    EMAIL_QUEUE_MAX_RETRIES: int = int(os.getenv("EMAIL_QUEUE_MAX_RETRIES", "3"))
    EMAIL_QUEUE_RETRY_DELAY_SECONDS: int = int(os.getenv("EMAIL_QUEUE_RETRY_DELAY_SECONDS", "2"))

    OAUTH_ENABLED: bool = os.getenv("OAUTH_ENABLED", "false").lower() == "true"
    OAUTH_ALLOWED_PROVIDERS: str = os.getenv("OAUTH_ALLOWED_PROVIDERS", "google,github")
    OAUTH_STATE_EXPIRE_MINUTES: int = int(os.getenv("OAUTH_STATE_EXPIRE_MINUTES", "10"))
    OAUTH_CALLBACK_RESPONSE_MODE: str = os.getenv(
        "OAUTH_CALLBACK_RESPONSE_MODE", "redirect"
    ).lower()
    OAUTH_FRONTEND_SUCCESS_PATH: str = os.getenv("OAUTH_FRONTEND_SUCCESS_PATH", "/login/success")
    OAUTH_FRONTEND_FAILURE_PATH: str = os.getenv("OAUTH_FRONTEND_FAILURE_PATH", "/login")

    OAUTH_GOOGLE_CLIENT_ID: str = os.getenv("OAUTH_GOOGLE_CLIENT_ID", "")
    OAUTH_GOOGLE_CLIENT_SECRET: str = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "")
    OAUTH_GOOGLE_AUTHORIZE_URL: str = os.getenv(
        "OAUTH_GOOGLE_AUTHORIZE_URL", "https://accounts.google.com/o/oauth2/v2/auth"
    )
    OAUTH_GOOGLE_TOKEN_URL: str = os.getenv(
        "OAUTH_GOOGLE_TOKEN_URL", "https://oauth2.googleapis.com/token"
    )
    OAUTH_GOOGLE_USERINFO_URL: str = os.getenv(
        "OAUTH_GOOGLE_USERINFO_URL", "https://openidconnect.googleapis.com/v1/userinfo"
    )

    OAUTH_GITHUB_CLIENT_ID: str = os.getenv("OAUTH_GITHUB_CLIENT_ID", "")
    OAUTH_GITHUB_CLIENT_SECRET: str = os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "")
    OAUTH_GITHUB_AUTHORIZE_URL: str = os.getenv(
        "OAUTH_GITHUB_AUTHORIZE_URL", "https://github.com/login/oauth/authorize"
    )
    OAUTH_GITHUB_TOKEN_URL: str = os.getenv(
        "OAUTH_GITHUB_TOKEN_URL", "https://github.com/login/oauth/access_token"
    )
    OAUTH_GITHUB_USERINFO_URL: str = os.getenv(
        "OAUTH_GITHUB_USERINFO_URL", "https://api.github.com/user"
    )
    OAUTH_GITHUB_SCOPES: str = os.getenv("OAUTH_GITHUB_SCOPES", "read:user user:email repo")
    OAUTH_GITHUB_SYNC_ON_LOGIN: bool = (
        os.getenv("OAUTH_GITHUB_SYNC_ON_LOGIN", "false").lower() == "true"
    )
    GITHUB_APP_ID: str = os.getenv("GITHUB_APP_ID", "")
    GITHUB_APP_SLUG: str = os.getenv("GITHUB_APP_SLUG", "")
    GITHUB_APP_PRIVATE_KEY: str = os.getenv("GITHUB_APP_PRIVATE_KEY", "")
    GITHUB_APP_PRIVATE_KEY_PATH: str = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH", "")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    SSE_HEARTBEAT_SECONDS: int = int(os.getenv("SSE_HEARTBEAT_SECONDS", "20"))
    SSE_RETRY_MILLIS: int = int(os.getenv("SSE_RETRY_MILLIS", "5000"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # When login is globally disabled, auth entry integrations must also stay off.
        if not self.LOGIN_ENABLED:
            object.__setattr__(self, "PASSWORD_AUTH_ENABLED", False)
            object.__setattr__(self, "EMAIL_ENABLED", False)
            object.__setattr__(self, "OAUTH_ENABLED", False)

        if self.DB_DRIVER.startswith("sqlite"):
            db_file = self.ROOT_DIR / self.DB_NAME
            object.__setattr__(self, "DATABASE_URL", f"{self.DB_DRIVER}:///{db_file.as_posix()}")
        else:
            object.__setattr__(
                self,
                "DATABASE_URL",
                (
                    f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}"
                    f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                ),
            )

        if self.REDIS_PASSWORD:
            redis_url = (
                f"redis://:{self.REDIS_PASSWORD}"
                f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        else:
            redis_url = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        object.__setattr__(self, "REDIS_URL", redis_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def oauth_provider_list(self) -> list[str]:
        allowed = [provider.strip().lower() for provider in self.OAUTH_ALLOWED_PROVIDERS.split(",")]
        allowed = [provider for provider in allowed if provider]
        supported = {"google", "github"}
        return [provider for provider in allowed if provider in supported]

    def get_oauth_provider_configs(self) -> dict[str, dict[str, str]]:
        provider_configs: dict[str, dict[str, str]] = {}
        if "google" in self.oauth_provider_list:
            provider_configs["google"] = {
                "client_id": self.OAUTH_GOOGLE_CLIENT_ID,
                "client_secret": self.OAUTH_GOOGLE_CLIENT_SECRET,
                "authorize_url": self.OAUTH_GOOGLE_AUTHORIZE_URL,
                "token_url": self.OAUTH_GOOGLE_TOKEN_URL,
                "userinfo_url": self.OAUTH_GOOGLE_USERINFO_URL,
            }
        if "github" in self.oauth_provider_list:
            provider_configs["github"] = {
                "client_id": self.OAUTH_GITHUB_CLIENT_ID,
                "client_secret": self.OAUTH_GITHUB_CLIENT_SECRET,
                "authorize_url": self.OAUTH_GITHUB_AUTHORIZE_URL,
                "token_url": self.OAUTH_GITHUB_TOKEN_URL,
                "userinfo_url": self.OAUTH_GITHUB_USERINFO_URL,
            }
        return provider_configs

    def get_smtp_validation_errors(self) -> list[str]:
        if not self.EMAIL_ENABLED:
            return []

        errors: list[str] = []
        if not self.SMTP_HOST.strip():
            errors.append("SMTP_HOST is required when EMAIL_ENABLED=true.")
        if self.SMTP_PORT <= 0:
            errors.append("SMTP_PORT must be greater than 0.")
        if not self.EMAIL_FROM.strip():
            errors.append("EMAIL_FROM is required when EMAIL_ENABLED=true.")
        if self.SMTP_USE_SSL and self.SMTP_USE_STARTTLS:
            errors.append("SMTP_USE_SSL and SMTP_USE_STARTTLS cannot both be true.")

        has_username = bool(self.SMTP_USERNAME.strip())
        has_password = bool(self.SMTP_PASSWORD.strip())
        if has_username != has_password:
            errors.append("SMTP_USERNAME and SMTP_PASSWORD must be set together.")

        return errors

    def get_oauth_validation_errors(self) -> list[str]:
        if not self.OAUTH_ENABLED:
            return []

        errors: list[str] = []
        provider_configs = self.get_oauth_provider_configs()
        if not provider_configs:
            errors.append("At least one OAuth provider must be enabled when OAUTH_ENABLED=true.")

        for provider, config in provider_configs.items():
            if not config["client_id"].strip():
                errors.append(f"{provider.upper()} client id is required when OAuth is enabled.")
            if not config["client_secret"].strip():
                errors.append(
                    f"{provider.upper()} client secret is required when OAuth is enabled."
                )

        return errors

    def get_github_app_private_key(self) -> str:
        private_key = self.GITHUB_APP_PRIVATE_KEY.strip()
        if private_key:
            return private_key.replace("\\n", "\n")

        private_key_path = self.GITHUB_APP_PRIVATE_KEY_PATH.strip()
        if not private_key_path:
            return ""

        path = Path(private_key_path).expanduser()
        if not path.is_absolute():
            path = self.ROOT_DIR / path
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError:
            return ""


SETTINGS = Settings()
