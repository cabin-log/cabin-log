from fastapi import APIRouter, Depends

from app.core.error import GameErrorCode, game_error_responses
from app.deps import get_current_user
from app.models.game import RewardPackageClaimResponse, RewardPackageResponse
from app.models.user import UserResponse
from app.services.game import GameService

router = APIRouter()


@router.get("/packages", response_model=list[RewardPackageResponse])
async def reward_packages(
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> list[RewardPackageResponse]:
    return await service.list_reward_packages(user_id=current_user.id)


@router.post(
    "/packages/{package_id}/claim",
    response_model=RewardPackageClaimResponse,
    responses=game_error_responses(
        GameErrorCode.REWARD_PACKAGE_NOT_FOUND,
        GameErrorCode.REWARD_PACKAGE_ALREADY_CLAIMED,
    ),
)
async def reward_package_claim(
    package_id: int,
    current_user: UserResponse = Depends(get_current_user),
    service: GameService = Depends(GameService),
) -> RewardPackageClaimResponse:
    return await service.claim_reward_package(user_id=current_user.id, package_id=package_id)
