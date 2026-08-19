from typing import Any

from fastapi import APIRouter, Depends, Header, Request

from app.core.error import GitHubErrorCode, github_error_responses
from app.services.github import GitHubService

router = APIRouter()


@router.post(
    "/github",
    responses=github_error_responses(
        GitHubErrorCode.GITHUB_WEBHOOK_SECRET_MISSING,
        GitHubErrorCode.GITHUB_WEBHOOK_INVALID_SIGNATURE,
        GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD,
        GitHubErrorCode.GITHUB_PROFILE_NOT_FOUND,
    ),
)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(alias="X-GitHub-Event"),
    x_github_delivery: str = Header(alias="X-GitHub-Delivery"),
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    service: GitHubService = Depends(GitHubService),
) -> dict[str, Any]:
    body = await request.body()
    return await service.ingest_webhook(
        event_name=x_github_event,
        delivery_id=x_github_delivery,
        signature=x_hub_signature_256,
        body=body,
    )
