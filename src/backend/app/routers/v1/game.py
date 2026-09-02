from datetime import date

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models.game import (
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
