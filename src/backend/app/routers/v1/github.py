from fastapi import APIRouter, Depends, Query

from app.core.error import GitHubErrorCode, github_error_responses
from app.deps import get_current_user
from app.models.activity import ActivityResponse
from app.models.github import (
    GitHubAppInstallUrlResponse,
    GitHubInstallationResponse,
    GitHubInstallationSyncResponse,
    GitHubOAuthSyncRequest,
    GitHubOAuthSyncResponse,
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


@router.get("/app/install-url", response_model=GitHubAppInstallUrlResponse)
async def github_app_install_url(
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> GitHubAppInstallUrlResponse:
    _ = current_user
    return service.get_app_install_url()


@router.get("/activities", response_model=list[ActivityResponse])
async def github_activities(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    service: GitHubService = Depends(GitHubService),
) -> list[ActivityResponse]:
    return await service.list_current_user_activities(user_id=current_user.id, limit=limit)


@router.post(
    "/sync",
    response_model=GitHubOAuthSyncResponse,
    responses=github_error_responses(
        GitHubErrorCode.GITHUB_PROFILE_NOT_FOUND,
        GitHubErrorCode.GITHUB_API_REQUEST_FAILED,
    ),
)
async def github_oauth_sync(
    form: GitHubOAuthSyncRequest,
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> GitHubOAuthSyncResponse:
    return await service.sync_current_user_oauth_snapshot(
        user_id=current_user.id,
        access_token=form.access_token.get_secret_value(),
    )


@router.get("/repositories", response_model=list[GitHubRepositoryResponse])
async def github_repositories(
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> list[GitHubRepositoryResponse]:
    return await service.list_current_user_repositories(user_id=current_user.id)


@router.get("/installations", response_model=list[GitHubInstallationResponse])
async def github_installations(
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> list[GitHubInstallationResponse]:
    return await service.list_current_user_installations(user_id=current_user.id)


@router.post(
    "/installations/{github_installation_id}/sync-repositories",
    response_model=GitHubInstallationSyncResponse,
    responses=github_error_responses(
        GitHubErrorCode.GITHUB_APP_CONFIG_INVALID,
        GitHubErrorCode.GITHUB_API_REQUEST_FAILED,
        GitHubErrorCode.GITHUB_INSTALLATION_NOT_FOUND,
    ),
)
async def github_installation_sync_repositories(
    github_installation_id: int,
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> GitHubInstallationSyncResponse:
    return await service.sync_current_user_installation_repositories(
        user_id=current_user.id,
        github_installation_id=github_installation_id,
    )


@router.get("/stack-summary", response_model=GitHubStackSummaryResponse)
async def github_stack_summary(
    current_user: UserResponse = Depends(get_current_user),
    service: GitHubService = Depends(GitHubService),
) -> GitHubStackSummaryResponse:
    return await service.get_current_stack_summary(user_id=current_user.id)
