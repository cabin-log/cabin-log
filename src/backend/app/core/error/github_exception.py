from enum import Enum

from fastapi import status

from .error import (
    ServiceErrorCode,
    ServiceException,
    build_error_models,
    build_error_responses_from_codes,
)


class GitHubErrorCode(Enum):
    GITHUB_PROFILE_NOT_FOUND = ServiceErrorCode(
        "GITHUB_PROFILE_NOT_FOUND",
        "GitHub profile is not linked to this user.",
        status.HTTP_404_NOT_FOUND,
    )
    GITHUB_API_REQUEST_FAILED = ServiceErrorCode(
        "GITHUB_API_REQUEST_FAILED",
        "GitHub API request failed.",
        status.HTTP_502_BAD_GATEWAY,
    )
    GITHUB_WEBHOOK_SECRET_MISSING = ServiceErrorCode(
        "GITHUB_WEBHOOK_SECRET_MISSING",
        "GitHub webhook secret is not configured.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    GITHUB_WEBHOOK_INVALID_SIGNATURE = ServiceErrorCode(
        "GITHUB_WEBHOOK_INVALID_SIGNATURE",
        "GitHub webhook signature is invalid.",
        status.HTTP_401_UNAUTHORIZED,
    )
    GITHUB_WEBHOOK_MALFORMED_PAYLOAD = ServiceErrorCode(
        "GITHUB_WEBHOOK_MALFORMED_PAYLOAD",
        "GitHub webhook payload is malformed.",
        status.HTTP_400_BAD_REQUEST,
    )

    @property
    def code(self) -> ServiceErrorCode:
        return self.value


class GitHubException(ServiceException):
    def __init__(
        self,
        code: GitHubErrorCode,
        message: str | None = None,
        details: dict | None = None,
    ):
        super().__init__(code=code.code, message=message, details=details)


GITHUB_ERROR_CODE_VALUES = tuple(error_code.code.error for error_code in GitHubErrorCode)


GitHubErrorDetail, GitHubErrorResponse = build_error_models(
    detail_model_name="GitHubErrorDetail",
    response_model_name="GitHubErrorResponse",
    error_values=GITHUB_ERROR_CODE_VALUES,
    example_error=GitHubErrorCode.GITHUB_PROFILE_NOT_FOUND.code.error,
)


def github_error_responses(*codes: GitHubErrorCode) -> dict[int, dict[str, object]]:
    return build_error_responses_from_codes(
        response_model=GitHubErrorResponse,
        codes=(code.code for code in codes),
    )
