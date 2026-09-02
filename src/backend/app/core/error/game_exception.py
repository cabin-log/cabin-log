from enum import Enum

from fastapi import status

from .error import (
    ServiceErrorCode,
    ServiceException,
    build_error_models,
    build_error_responses_from_codes,
)


class GameErrorCode(Enum):
    REWARD_PACKAGE_NOT_FOUND = ServiceErrorCode(
        "REWARD_PACKAGE_NOT_FOUND",
        "Reward package was not found.",
        status.HTTP_404_NOT_FOUND,
    )
    REWARD_PACKAGE_ALREADY_CLAIMED = ServiceErrorCode(
        "REWARD_PACKAGE_ALREADY_CLAIMED",
        "Reward package has already been claimed.",
        status.HTTP_409_CONFLICT,
    )

    @property
    def code(self) -> ServiceErrorCode:
        return self.value


class GameException(ServiceException):
    def __init__(
        self,
        code: GameErrorCode,
        message: str | None = None,
        details: dict | None = None,
    ):
        super().__init__(code=code.code, message=message, details=details)


GAME_ERROR_CODE_VALUES = tuple(error_code.code.error for error_code in GameErrorCode)


GameErrorDetail, GameErrorResponse = build_error_models(
    detail_model_name="GameErrorDetail",
    response_model_name="GameErrorResponse",
    error_values=GAME_ERROR_CODE_VALUES,
    example_error=GameErrorCode.REWARD_PACKAGE_NOT_FOUND.code.error,
)


def game_error_responses(*codes: GameErrorCode) -> dict[int, dict[str, object]]:
    return build_error_responses_from_codes(
        response_model=GameErrorResponse,
        codes=(code.code for code in codes),
    )
