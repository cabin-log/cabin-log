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
    CABIN_PLACEMENT_NOT_FOUND = ServiceErrorCode(
        "CABIN_PLACEMENT_NOT_FOUND",
        "Cabin placement was not found.",
        status.HTTP_404_NOT_FOUND,
    )
    CABIN_PLACEMENT_INVALID = ServiceErrorCode(
        "CABIN_PLACEMENT_INVALID",
        "Cabin placement is outside the cabin grid.",
        status.HTTP_400_BAD_REQUEST,
    )
    CABIN_PLACEMENT_CONFLICT = ServiceErrorCode(
        "CABIN_PLACEMENT_CONFLICT",
        "Cabin placement overlaps an existing object.",
        status.HTTP_409_CONFLICT,
    )
    CABIN_ITEM_NOT_OWNED = ServiceErrorCode(
        "CABIN_ITEM_NOT_OWNED",
        "Cabin object is not owned by the user.",
        status.HTTP_403_FORBIDDEN,
    )
    CABIN_SYSTEM_PLACEMENT_LOCKED = ServiceErrorCode(
        "CABIN_SYSTEM_PLACEMENT_LOCKED",
        "System cabin placements cannot be changed.",
        status.HTTP_403_FORBIDDEN,
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
