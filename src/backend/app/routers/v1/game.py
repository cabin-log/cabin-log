from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models.game import StackProfilesResponse
from app.models.user import UserResponse
from app.services.game import GameService

router = APIRouter()


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
