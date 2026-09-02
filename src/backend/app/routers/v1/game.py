from datetime import date

from fastapi import APIRouter, Depends, Response, status

from app.core.error import GameErrorCode, game_error_responses
from app.deps import get_current_user
from app.models.game import (
    CabinPlacementCreate,
    CabinPlacementResponse,
    CabinPlacementUpdate,
    CabinResponse,
    DailyActivitySummaryResponse,
    DailyRewardPackageResponse,
    GameStateResponse,
    StackProfilesResponse,
    UserGameSettingsResponse,
    UserGameSettingsUpdate,
)
from app.models.user import UserResponse
from app.services.game import GameService

router = APIRouter()


@router.get("/state", response_model=GameStateResponse)
async def game_state(
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> GameStateResponse:
    return await service.get_game_state(user_id=current_user.id)


@router.get("/settings", response_model=UserGameSettingsResponse)
async def game_settings(
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> UserGameSettingsResponse:
    return await service.get_user_settings(user_id=current_user.id)


@router.patch("/settings", response_model=UserGameSettingsResponse)
async def game_settings_update(
    form: UserGameSettingsUpdate,
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> UserGameSettingsResponse:
    return await service.update_user_settings(user_id=current_user.id, form=form)


@router.get("/cabin", response_model=CabinResponse)
async def game_cabin(
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> CabinResponse:
    return await service.get_cabin(user_id=current_user.id)


@router.post(
    "/cabin/placements",
    response_model=CabinPlacementResponse,
    status_code=status.HTTP_201_CREATED,
    responses=game_error_responses(
        GameErrorCode.CABIN_ITEM_NOT_OWNED,
        GameErrorCode.CABIN_PLACEMENT_INVALID,
        GameErrorCode.CABIN_PLACEMENT_CONFLICT,
        GameErrorCode.CABIN_SYSTEM_PLACEMENT_LOCKED,
    ),
)
async def game_cabin_placement_create(
    form: CabinPlacementCreate,
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> CabinPlacementResponse:
    return await service.create_cabin_placement(user_id=current_user.id, form=form)


@router.patch(
    "/cabin/placements/{placement_id}",
    response_model=CabinPlacementResponse,
    responses=game_error_responses(
        GameErrorCode.CABIN_PLACEMENT_NOT_FOUND,
        GameErrorCode.CABIN_PLACEMENT_INVALID,
        GameErrorCode.CABIN_PLACEMENT_CONFLICT,
        GameErrorCode.CABIN_SYSTEM_PLACEMENT_LOCKED,
    ),
)
async def game_cabin_placement_update(
    placement_id: int,
    form: CabinPlacementUpdate,
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> CabinPlacementResponse:
    return await service.update_cabin_placement(
        user_id=current_user.id,
        placement_id=placement_id,
        form=form,
    )


@router.delete(
    "/cabin/placements/{placement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=game_error_responses(
        GameErrorCode.CABIN_PLACEMENT_NOT_FOUND,
        GameErrorCode.CABIN_SYSTEM_PLACEMENT_LOCKED,
    ),
)
async def game_cabin_placement_delete(
    placement_id: int,
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> Response:
    await service.delete_cabin_placement(user_id=current_user.id, placement_id=placement_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stacks", response_model=StackProfilesResponse)
async def game_stack_profiles(
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> StackProfilesResponse:
    return await service.get_stack_profiles(user_id=current_user.id)


@router.post("/stacks/recalculate", response_model=StackProfilesResponse)
async def game_stack_profiles_recalculate(
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> StackProfilesResponse:
    return await service.recalculate_stack_profiles(user_id=current_user.id)


@router.get("/activity/daily-summary", response_model=DailyActivitySummaryResponse)
async def game_daily_activity_summary(
    reward_date: date | None = None,
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> DailyActivitySummaryResponse:
    return await service.get_daily_activity_summary(
        user_id=current_user.id,
        reward_date=reward_date,
    )


@router.post("/activity/daily-reward", response_model=DailyRewardPackageResponse)
async def game_daily_reward_package(
    reward_date: date | None = None,
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> DailyRewardPackageResponse:
    return await service.create_daily_reward_package(
        user_id=current_user.id,
        reward_date=reward_date,
    )
