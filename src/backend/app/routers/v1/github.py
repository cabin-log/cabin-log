from fastapi import APIRouter, Depends, Query

from app.core.error import GitHubErrorCode, github_error_responses
from app.deps import get_current_user
from app.models.activity import ActivityResponse
from app.models.github import (
    GitHubProfileResponse,
    GitHubRepositoryResponse,
    GitHubStackSummaryResponse,
)
from app.models.user import UserResponse
from app.services.github import GitHubService

router = APIRouter()


@router.get(
    "/me",
    response_model=GitHubProfileResponse,
    responses=github_error_responses(GitHubErrorCode.GITHUB_PROFILE_NOT_FOUND),
)
async def github_me(
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> GitHubProfileResponse:
    return await service.get_current_profile(current_user.id)


@router.get("/activities", response_model=list[ActivityResponse])
async def github_activities(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    service: GitHubService = Depends(GitHubService),
) -> list[ActivityResponse]:
    return await service.list_current_user_activities(user_id=current_user.id, limit=limit)


@router.get("/repositories", response_model=list[GitHubRepositoryResponse])
async def github_repositories(
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> list[GitHubRepositoryResponse]:
    return await service.list_current_user_repositories(user_id=current_user.id)


@router.get("/stack-summary", response_model=GitHubStackSummaryResponse)
async def github_stack_summary(
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> GitHubStackSummaryResponse:
    return await service.get_current_stack_summary(user_id=current_user.id)
