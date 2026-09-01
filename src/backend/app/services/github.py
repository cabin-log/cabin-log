import asyncio
import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request as URLRequest, urlopen

from jose import jwt

from app.core.config.settings import SETTINGS
from app.core.error import GitHubErrorCode, GitHubException
from app.core.observability.logging import get_logger
from app.models.activity import Activities, ActivityCreate, ActivityCreateResult, ActivityType
from app.models.github import (
    GitHubAppInstallUrlResponse,
    GitHubInstallationResponse,
    GitHubInstallationSyncResponse,
    GitHubInstallationUpsert,
    GitHubOAuthSyncResponse,
    GitHubProfileResponse,
    GitHubProfiles,
    GitHubRepositoryResponse,
    GitHubRepositoryUpsert,
    GitHubStackSummaryResponse,
)

logger = get_logger("app.service.github")


class GitHubService:
    def get_app_install_url(self) -> GitHubAppInstallUrlResponse:
        app_slug = SETTINGS.GITHUB_APP_SLUG.strip()
        if not app_slug:
            return GitHubAppInstallUrlResponse(configured=False)
        return GitHubAppInstallUrlResponse(
            configured=True,
            install_url=f"https://github.com/apps/{quote(app_slug)}/installations/new",
        )

    async def get_current_profile(self, user_id: int) -> GitHubProfileResponse:
        profile = await GitHubProfiles.get_profile_by_user_id(user_id)
        if profile is None:
            raise GitHubException(code=GitHubErrorCode.GITHUB_PROFILE_NOT_FOUND)
        return profile

    async def list_current_user_activities(self, user_id: int, limit: int = 50):
        return await Activities.list_user_activities(user_id=user_id, limit=limit)

    async def list_current_user_repositories(self, user_id: int) -> list[GitHubRepositoryResponse]:
        return await GitHubProfiles.list_repositories(user_id=user_id)

    async def list_current_user_installations(
        self,
        user_id: int,
    ) -> list[GitHubInstallationResponse]:
        return await GitHubProfiles.list_installations(user_id=user_id)

    async def sync_current_user_installation_repositories(
        self,
        *,
        user_id: int,
        github_installation_id: int,
    ) -> GitHubInstallationSyncResponse:
        installation = await GitHubProfiles.get_installation_by_github_id(github_installation_id)
        if (
            installation is None
            or installation.user_id != user_id
            or installation.deleted_at is not None
        ):
            raise GitHubException(
                code=GitHubErrorCode.GITHUB_INSTALLATION_NOT_FOUND,
                details={"github_installation_id": github_installation_id},
            )

        app_client = GitHubAppClient.from_settings()
        installation_token = await app_client.create_installation_access_token(
            github_installation_id
        )
        api_client = GitHubAPIClient(access_token=installation_token)
        repositories = await api_client.fetch_installation_repositories()
        upserts = await self._build_repository_upserts(
            user_id=user_id,
            repositories=repositories,
            client=api_client,
            github_installation_id=github_installation_id,
        )
        persisted = await GitHubProfiles.upsert_repositories(upserts)
        return GitHubInstallationSyncResponse(
            github_installation_id=github_installation_id,
            repository_count=len(persisted),
            repositories=persisted,
        )

    async def get_current_stack_summary(self, user_id: int) -> GitHubStackSummaryResponse:
        return await GitHubProfiles.get_stack_summary(user_id=user_id)

    async def sync_current_user_oauth_snapshot(
        self,
        *,
        user_id: int,
        access_token: str,
    ) -> GitHubOAuthSyncResponse:
        profile = await GitHubProfiles.get_profile_by_user_id(user_id)
        if profile is None:
            raise GitHubException(code=GitHubErrorCode.GITHUB_PROFILE_NOT_FOUND)
        return await self.sync_oauth_snapshot(
            user_id=user_id,
            access_token=access_token,
            github_login=profile.login,
        )

    async def sync_oauth_snapshot(
        self,
        *,
        user_id: int,
        access_token: str,
        github_login: str | None,
    ) -> GitHubOAuthSyncResponse:
        client = GitHubAPIClient(access_token=access_token)
        repositories = await client.fetch_authenticated_user_repositories()
        upserts = await self._build_repository_upserts(
            user_id=user_id,
            repositories=repositories,
            client=client,
        )
        persisted_repositories = await GitHubProfiles.upsert_repositories(upserts)

        created_count = 0
        duplicate_count = 0
        if github_login:
            repository_lookup = {
                repository.github_repo_id: repository.full_name
                for repository in persisted_repositories
            }
            activity_results: list[ActivityCreateResult] = []
            for repository in persisted_repositories:
                commits = await client.fetch_repository_commits_by_author(
                    full_name=repository.full_name,
                    author_login=github_login,
                )
                activity_results.extend(
                    await self._persist_oauth_commit_activities(
                        user_id=user_id,
                        repository=repository,
                        commits=commits,
                    )
                )

            pull_requests = await client.search_user_pull_requests(author_login=github_login)
            activity_results.extend(
                await self._persist_oauth_pull_request_activities(
                    user_id=user_id,
                    pull_requests=pull_requests,
                    repository_lookup=repository_lookup,
                )
            )
            merged_pull_requests = await client.search_user_merged_pull_requests(
                author_login=github_login
            )
            activity_results.extend(
                await self._persist_oauth_merged_pull_request_activities(
                    user_id=user_id,
                    pull_requests=merged_pull_requests,
                    repository_lookup=repository_lookup,
                )
            )
            issues = await client.search_user_issues(author_login=github_login)
            activity_results.extend(
                await self._persist_oauth_issue_activities(
                    user_id=user_id,
                    issues=issues,
                    repository_lookup=repository_lookup,
                )
            )

            created_count = sum(1 for result in activity_results if not result.duplicate)
            duplicate_count = sum(1 for result in activity_results if result.duplicate)

        return GitHubOAuthSyncResponse(
            repository_count=len(persisted_repositories),
            created_activity_count=created_count,
            duplicate_activity_count=duplicate_count,
        )

    async def sync_user_repositories(
        self,
        *,
        user_id: int,
        access_token: str,
    ) -> list[GitHubRepositoryResponse]:
        client = GitHubAPIClient(access_token=access_token)
        repositories = await client.fetch_authenticated_user_repositories()
        upserts = await self._build_repository_upserts(
            user_id=user_id,
            repositories=repositories,
            client=client,
        )
        return await GitHubProfiles.upsert_repositories(upserts)

    async def _build_repository_upserts(
        self,
        *,
        user_id: int,
        repositories: list[dict[str, Any]],
        client: "GitHubAPIClient",
        github_installation_id: int | None = None,
    ) -> list[GitHubRepositoryUpsert]:
        upserts: list[GitHubRepositoryUpsert] = []
        for repository in repositories:
            full_name = repository.get("full_name")
            repo_id = repository.get("id")
            owner = repository.get("owner")
            name = repository.get("name")
            if not isinstance(full_name, str) or not isinstance(repo_id, int):
                continue
            if not isinstance(owner, Mapping) or not isinstance(owner.get("login"), str):
                continue
            if not isinstance(name, str):
                continue
            languages = await client.fetch_repository_languages(full_name)
            upserts.append(
                GitHubRepositoryUpsert(
                    user_id=user_id,
                    github_installation_id=github_installation_id,
                    github_repo_id=repo_id,
                    owner_login=str(owner["login"]),
                    name=name,
                    full_name=full_name,
                    private=bool(repository.get("private", False)),
                    html_url=(
                        str(repository["html_url"])
                        if isinstance(repository.get("html_url"), str)
                        else None
                    ),
                    default_branch=(
                        str(repository["default_branch"])
                        if isinstance(repository.get("default_branch"), str)
                        else None
                    ),
                    primary_language=(
                        str(repository["language"])
                        if isinstance(repository.get("language"), str)
                        else None
                    ),
                    pushed_at=_parse_github_datetime(repository.get("pushed_at")),
                    languages=languages,
                )
            )
        return upserts

    async def _persist_oauth_commit_activities(
        self,
        *,
        user_id: int,
        repository: GitHubRepositoryResponse,
        commits: list[dict[str, Any]],
    ) -> list[ActivityCreateResult]:
        results: list[ActivityCreateResult] = []
        for commit_payload in commits:
            sha = commit_payload.get("sha")
            commit = commit_payload.get("commit")
            if not isinstance(sha, str) or not isinstance(commit, dict):
                continue
            author = commit.get("author")
            if not isinstance(author, dict):
                author = {}
            results.append(
                await Activities.create_activity_once(
                    ActivityCreate(
                        user_id=user_id,
                        type=ActivityType.COMMIT,
                        source="OAUTH_API",
                        repository_github_id=repository.github_repo_id,
                        repository_full_name=repository.full_name,
                        github_external_id=f"github:commit:{sha}",
                        occurred_at=_parse_github_datetime(author.get("date")) or datetime.now(UTC),
                        metadata={
                            "sha": sha,
                            "message": commit.get("message"),
                            "html_url": commit_payload.get("html_url"),
                        },
                    )
                )
            )
        return results

    async def _persist_oauth_pull_request_activities(
        self,
        *,
        user_id: int,
        pull_requests: list[dict[str, Any]],
        repository_lookup: dict[int, str],
    ) -> list[ActivityCreateResult]:
        results: list[ActivityCreateResult] = []
        for pull_request in pull_requests:
            github_id = pull_request.get("id")
            if not isinstance(github_id, int):
                continue
            repository_github_id = self._extract_repository_id_from_search_item(pull_request)
            repository_full_name = self._extract_repository_full_name_from_search_item(pull_request)
            results.append(
                await Activities.create_activity_once(
                    ActivityCreate(
                        user_id=user_id,
                        type=ActivityType.PULL_REQUEST_OPENED,
                        source="OAUTH_API",
                        repository_github_id=repository_github_id,
                        repository_full_name=repository_lookup.get(
                            repository_github_id or -1,
                            repository_full_name,
                        ),
                        github_external_id=f"github:pull_request:{github_id}:opened",
                        occurred_at=_parse_github_datetime(pull_request.get("created_at"))
                        or datetime.now(UTC),
                        metadata={
                            "number": pull_request.get("number"),
                            "title": pull_request.get("title"),
                            "html_url": pull_request.get("html_url"),
                            "state": pull_request.get("state"),
                        },
                    )
                )
            )
        return results

    async def _persist_oauth_merged_pull_request_activities(
        self,
        *,
        user_id: int,
        pull_requests: list[dict[str, Any]],
        repository_lookup: dict[int, str],
    ) -> list[ActivityCreateResult]:
        results: list[ActivityCreateResult] = []
        for pull_request in pull_requests:
            github_id = pull_request.get("id")
            if not isinstance(github_id, int):
                continue
            repository_github_id = self._extract_repository_id_from_search_item(pull_request)
            repository_full_name = self._extract_repository_full_name_from_search_item(pull_request)
            results.append(
                await Activities.create_activity_once(
                    ActivityCreate(
                        user_id=user_id,
                        type=ActivityType.PULL_REQUEST_MERGED,
                        source="OAUTH_API",
                        repository_github_id=repository_github_id,
                        repository_full_name=repository_lookup.get(
                            repository_github_id or -1,
                            repository_full_name,
                        ),
                        github_external_id=f"github:pull_request:{github_id}:merged",
                        occurred_at=_parse_github_datetime(pull_request.get("closed_at"))
                        or _parse_github_datetime(pull_request.get("updated_at"))
                        or datetime.now(UTC),
                        metadata={
                            "number": pull_request.get("number"),
                            "title": pull_request.get("title"),
                            "html_url": pull_request.get("html_url"),
                            "state": pull_request.get("state"),
                        },
                    )
                )
            )
        return results

    async def _persist_oauth_issue_activities(
        self,
        *,
        user_id: int,
        issues: list[dict[str, Any]],
        repository_lookup: dict[int, str],
    ) -> list[ActivityCreateResult]:
        results: list[ActivityCreateResult] = []
        for issue in issues:
            github_id = issue.get("id")
            if not isinstance(github_id, int):
                continue
            repository_github_id = self._extract_repository_id_from_search_item(issue)
            repository_full_name = self._extract_repository_full_name_from_search_item(issue)
            results.append(
                await Activities.create_activity_once(
                    ActivityCreate(
                        user_id=user_id,
                        type=ActivityType.ISSUE,
                        source="OAUTH_API",
                        repository_github_id=repository_github_id,
                        repository_full_name=repository_lookup.get(
                            repository_github_id or -1,
                            repository_full_name,
                        ),
                        github_external_id=f"github:issue:{github_id}:opened",
                        occurred_at=_parse_github_datetime(issue.get("created_at"))
                        or datetime.now(UTC),
                        metadata={
                            "number": issue.get("number"),
                            "title": issue.get("title"),
                            "html_url": issue.get("html_url"),
                            "state": issue.get("state"),
                        },
                    )
                )
            )
        return results

    def _extract_repository_id_from_search_item(self, item: dict[str, Any]) -> int | None:
        repository = item.get("repository")
        if isinstance(repository, Mapping) and isinstance(repository.get("id"), int):
            return int(repository["id"])
        return None

    def _extract_repository_full_name_from_search_item(self, item: dict[str, Any]) -> str | None:
        repository = item.get("repository")
        if isinstance(repository, Mapping) and isinstance(repository.get("full_name"), str):
            return str(repository["full_name"])
        repository_url = item.get("repository_url")
        if not isinstance(repository_url, str):
            return None
        prefix = "https://api.github.com/repos/"
        if not repository_url.startswith(prefix):
            return None
        full_name = repository_url.removeprefix(prefix)
        return full_name if "/" in full_name else None

    async def ingest_webhook(
        self,
        *,
        event_name: str,
        delivery_id: str,
        signature: str | None,
        body: bytes,
    ) -> dict[str, Any]:
        self._verify_signature(signature=signature, body=body)
        payload = self._parse_payload(body)

        if event_name == "installation":
            return await self._ingest_installation_event(
                delivery_id=delivery_id,
                payload=payload,
            )

        if event_name == "installation_repositories":
            return await self._ingest_installation_repositories_event(
                delivery_id=delivery_id,
                payload=payload,
            )

        if event_name == "pull_request":
            result = await self._ingest_pull_request_event(
                delivery_id=delivery_id,
                payload=payload,
            )
            if result is None:
                return {
                    "status": "ignored",
                    "event": event_name,
                    "delivery_id": delivery_id,
                    "reason": "unsupported_pull_request_action",
                }
            return {
                "status": "duplicate" if result.duplicate else "created",
                "event": event_name,
                "delivery_id": delivery_id,
                "activity": result.activity.model_dump(mode="json"),
            }

        if event_name != "push":
            logger.info(
                "GitHub webhook ignored unsupported event (event=%s, delivery_id=%s).",
                event_name,
                delivery_id,
            )
            return {
                "status": "ignored",
                "event": event_name,
                "delivery_id": delivery_id,
                "reason": "unsupported_event",
            }

        result = await self._ingest_push_event(delivery_id=delivery_id, payload=payload)
        return {
            "status": "duplicate" if result.duplicate else "created",
            "event": event_name,
            "delivery_id": delivery_id,
            "activity": result.activity.model_dump(mode="json"),
        }

    async def _ingest_push_event(
        self,
        *,
        delivery_id: str,
        payload: dict[str, Any],
    ) -> ActivityCreateResult:
        sender = payload.get("sender")
        if not isinstance(sender, dict):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD)

        github_installation_id = self._extract_installation_id(payload)
        user_id = await self._resolve_webhook_user_id(payload)
        if user_id is None:
            logger.info(
                "GitHub webhook ignored unlinked push (installation_id=%s, delivery_id=%s).",
                github_installation_id,
                delivery_id,
            )
            raise GitHubException(
                code=GitHubErrorCode.GITHUB_PROFILE_NOT_FOUND,
                message="GitHub webhook installation or sender is not linked to a Cabinlog user.",
                details={"delivery_id": delivery_id},
            )

        repository = payload.get("repository")
        if not isinstance(repository, dict):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD)

        repository_github_id = repository.get("id")
        if repository_github_id is not None and not isinstance(repository_github_id, int):
            repository_github_id = None

        commits = payload.get("commits")
        commit_count = len(commits) if isinstance(commits, list) else 0
        occurred_at = self._resolve_push_occurred_at(payload)
        metadata = {
            "ref": payload.get("ref"),
            "before": payload.get("before"),
            "after": payload.get("after"),
            "commit_count": commit_count,
            "pusher": payload.get("pusher") if isinstance(payload.get("pusher"), dict) else None,
        }

        return await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=ActivityType.PUSH,
                github_installation_id=github_installation_id,
                repository_github_id=repository_github_id,
                repository_full_name=(
                    repository.get("full_name")
                    if isinstance(repository.get("full_name"), str)
                    else None
                ),
                github_delivery_id=delivery_id,
                occurred_at=occurred_at,
                metadata=metadata,
            )
        )

    async def _ingest_pull_request_event(
        self,
        *,
        delivery_id: str,
        payload: dict[str, Any],
    ) -> ActivityCreateResult | None:
        sender = payload.get("sender")
        pull_request = payload.get("pull_request")
        repository = payload.get("repository")
        if not isinstance(sender, dict) or not isinstance(pull_request, dict):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD)
        if not isinstance(repository, dict):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD)

        github_installation_id = self._extract_installation_id(payload)
        user_id = await self._resolve_webhook_user_id(payload)
        if user_id is None:
            raise GitHubException(
                code=GitHubErrorCode.GITHUB_PROFILE_NOT_FOUND,
                message="GitHub webhook sender is not linked to a Cabinlog user.",
                details={"delivery_id": delivery_id},
            )

        action = payload.get("action")
        merged = bool(pull_request.get("merged"))
        if action == "opened":
            activity_type = ActivityType.PULL_REQUEST_OPENED
        elif action == "closed" and merged:
            activity_type = ActivityType.PULL_REQUEST_MERGED
        else:
            logger.info(
                "GitHub pull_request webhook ignored action (action=%s, delivery_id=%s).",
                action,
                delivery_id,
            )
            return None

        repository_github_id = repository.get("id")
        if repository_github_id is not None and not isinstance(repository_github_id, int):
            repository_github_id = None

        return await Activities.create_activity_once(
            ActivityCreate(
                user_id=user_id,
                type=activity_type,
                github_installation_id=github_installation_id,
                repository_github_id=repository_github_id,
                repository_full_name=(
                    repository.get("full_name")
                    if isinstance(repository.get("full_name"), str)
                    else None
                ),
                github_delivery_id=delivery_id,
                occurred_at=_parse_github_datetime(pull_request.get("updated_at"))
                or datetime.now(UTC),
                metadata={
                    "action": action,
                    "number": pull_request.get("number"),
                    "title": pull_request.get("title"),
                    "html_url": pull_request.get("html_url"),
                    "merged": merged,
                },
            )
        )

    async def _ingest_installation_event(
        self,
        *,
        delivery_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        installation_payload = self._require_installation_payload(payload)
        github_installation_id = self._require_int(installation_payload.get("id"))
        action = payload.get("action")

        if action == "deleted":
            deleted = await GitHubProfiles.mark_installation_deleted(github_installation_id)
            return {
                "status": "deleted" if deleted else "ignored",
                "event": "installation",
                "delivery_id": delivery_id,
                "github_installation_id": github_installation_id,
            }

        if action not in {"created", "new_permissions_accepted", "suspend", "unsuspend"}:
            return {
                "status": "ignored",
                "event": "installation",
                "delivery_id": delivery_id,
                "reason": "unsupported_installation_action",
            }

        user_id = await self._resolve_sender_user_id(payload)
        installation = await self._upsert_installation_from_payload(
            installation_payload,
            user_id=user_id,
            deleted_at=None,
            suspended_at=(
                datetime.now(UTC)
                if action == "suspend"
                else _parse_github_datetime(installation_payload.get("suspended_at"))
            ),
        )
        repositories = self._extract_repository_upserts(
            payload.get("repositories") if isinstance(payload.get("repositories"), list) else [],
            user_id=user_id,
            github_installation_id=github_installation_id,
        )
        if repositories and user_id is not None:
            await GitHubProfiles.upsert_repositories(repositories)
        return {
            "status": "upserted",
            "event": "installation",
            "delivery_id": delivery_id,
            "installation": installation.model_dump(mode="json"),
            "repository_count": len(repositories),
        }

    async def _ingest_installation_repositories_event(
        self,
        *,
        delivery_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        installation_payload = self._require_installation_payload(payload)
        github_installation_id = self._require_int(installation_payload.get("id"))
        installation = await GitHubProfiles.get_installation_by_github_id(github_installation_id)
        user_id = (
            installation.user_id
            if installation is not None
            else await self._resolve_sender_user_id(payload)
        )

        if installation is None:
            installation = await self._upsert_installation_from_payload(
                installation_payload,
                user_id=user_id,
            )

        added_payload = payload.get("repositories_added")
        removed_payload = payload.get("repositories_removed")
        added_repositories = self._extract_repository_upserts(
            added_payload if isinstance(added_payload, list) else [],
            user_id=user_id,
            github_installation_id=github_installation_id,
        )
        if added_repositories and user_id is not None:
            await GitHubProfiles.upsert_repositories(added_repositories)

        removed_ids = [
            repo_id
            for repo_id in (
                repository.get("id")
                for repository in (removed_payload if isinstance(removed_payload, list) else [])
                if isinstance(repository, dict)
            )
            if isinstance(repo_id, int)
        ]
        await GitHubProfiles.remove_installation_repositories(
            github_installation_id=github_installation_id,
            github_repo_ids=removed_ids,
        )

        return {
            "status": "updated",
            "event": "installation_repositories",
            "delivery_id": delivery_id,
            "installation": installation.model_dump(mode="json"),
            "repositories_added": len(added_repositories),
            "repositories_removed": len(removed_ids),
        }

    async def _upsert_installation_from_payload(
        self,
        installation_payload: dict[str, Any],
        *,
        user_id: int | None,
        deleted_at: datetime | None = None,
        suspended_at: datetime | None = None,
    ) -> GitHubInstallationResponse:
        account = installation_payload.get("account")
        if not isinstance(account, dict):
            account = {}
        return await GitHubProfiles.upsert_installation(
            GitHubInstallationUpsert(
                user_id=user_id,
                github_installation_id=self._require_int(installation_payload.get("id")),
                account_id=account.get("id") if isinstance(account.get("id"), int) else None,
                account_login=account.get("login")
                if isinstance(account.get("login"), str)
                else None,
                account_type=account.get("type") if isinstance(account.get("type"), str) else None,
                target_type=(
                    installation_payload.get("target_type")
                    if isinstance(installation_payload.get("target_type"), str)
                    else None
                ),
                repository_selection=(
                    installation_payload.get("repository_selection")
                    if isinstance(installation_payload.get("repository_selection"), str)
                    else None
                ),
                suspended_at=suspended_at,
                deleted_at=deleted_at,
            )
        )

    async def _resolve_webhook_user_id(self, payload: dict[str, Any]) -> int | None:
        github_installation_id = self._extract_installation_id(payload)
        if github_installation_id is not None:
            installation = await GitHubProfiles.get_installation_by_github_id(
                github_installation_id
            )
            if installation is not None and installation.deleted_at is None:
                return installation.user_id
        return await self._resolve_sender_user_id(payload)

    async def _resolve_sender_user_id(self, payload: dict[str, Any]) -> int | None:
        sender = payload.get("sender")
        if not isinstance(sender, dict):
            return None
        github_user_id = sender.get("id")
        if not isinstance(github_user_id, int):
            return None
        return await GitHubProfiles.get_user_id_by_github_user_id(github_user_id)

    def _extract_installation_id(self, payload: dict[str, Any]) -> int | None:
        installation = payload.get("installation")
        if not isinstance(installation, dict):
            return None
        installation_id = installation.get("id")
        return installation_id if isinstance(installation_id, int) else None

    def _require_installation_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        installation = payload.get("installation")
        if not isinstance(installation, dict):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD)
        return installation

    def _require_int(self, value: Any) -> int:
        if not isinstance(value, int):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD)
        return value

    def _extract_repository_upserts(
        self,
        repositories: list[Any],
        *,
        user_id: int | None,
        github_installation_id: int,
    ) -> list[GitHubRepositoryUpsert]:
        if user_id is None:
            return []
        upserts: list[GitHubRepositoryUpsert] = []
        for repository in repositories:
            if not isinstance(repository, dict):
                continue
            repo_id = repository.get("id")
            full_name = repository.get("full_name")
            name = repository.get("name")
            if not isinstance(repo_id, int) or not isinstance(full_name, str):
                continue
            if not isinstance(name, str):
                name = full_name.rsplit("/", 1)[-1]
            owner_login = self._extract_owner_login(repository, full_name)
            upserts.append(
                GitHubRepositoryUpsert(
                    user_id=user_id,
                    github_installation_id=github_installation_id,
                    github_repo_id=repo_id,
                    owner_login=owner_login,
                    name=name,
                    full_name=full_name,
                    private=bool(repository.get("private", False)),
                    html_url=(
                        repository.get("html_url")
                        if isinstance(repository.get("html_url"), str)
                        else None
                    ),
                    default_branch=(
                        repository.get("default_branch")
                        if isinstance(repository.get("default_branch"), str)
                        else None
                    ),
                    primary_language=(
                        repository.get("language")
                        if isinstance(repository.get("language"), str)
                        else None
                    ),
                    pushed_at=_parse_github_datetime(repository.get("pushed_at")),
                    languages={},
                )
            )
        return upserts

    def _extract_owner_login(self, repository: dict[str, Any], full_name: str) -> str:
        owner = repository.get("owner")
        if isinstance(owner, Mapping) and isinstance(owner.get("login"), str):
            return str(owner["login"])
        return full_name.split("/", 1)[0]

    def _verify_signature(self, *, signature: str | None, body: bytes) -> None:
        secret = SETTINGS.GITHUB_WEBHOOK_SECRET.strip()
        if not secret:
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_SECRET_MISSING)
        if not signature or not signature.startswith("sha256="):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_INVALID_SIGNATURE)

        expected = (
            "sha256="
            + hmac.new(
                secret.encode("utf-8"),
                body,
                hashlib.sha256,
            ).hexdigest()
        )
        if not hmac.compare_digest(expected, signature):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_INVALID_SIGNATURE)

    def _parse_payload(self, body: bytes) -> dict[str, Any]:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD) from error
        if not isinstance(payload, dict):
            raise GitHubException(code=GitHubErrorCode.GITHUB_WEBHOOK_MALFORMED_PAYLOAD)
        return payload

    def _resolve_push_occurred_at(self, payload: dict[str, Any]) -> datetime:
        head_commit = payload.get("head_commit")
        if isinstance(head_commit, dict):
            timestamp = head_commit.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    pass
        return datetime.now(UTC)


class GitHubAPIClient:
    def __init__(self, access_token: str):
        self.access_token = access_token

    async def fetch_authenticated_user_repositories(self) -> list[dict[str, Any]]:
        repositories: list[dict[str, Any]] = []
        page = 1
        while True:
            payload = await self._request_json(
                "https://api.github.com/user/repos?"
                + urlencode(
                    {
                        "per_page": "100",
                        "page": str(page),
                        "sort": "pushed",
                        "affiliation": "owner,collaborator,organization_member",
                    }
                )
            )
            if not isinstance(payload, list):
                return repositories
            repositories.extend(item for item in payload if isinstance(item, dict))
            if len(payload) < 100:
                return repositories
            page += 1

    async def fetch_installation_repositories(self) -> list[dict[str, Any]]:
        repositories: list[dict[str, Any]] = []
        page = 1
        while True:
            payload = await self._request_json(
                f"https://api.github.com/installation/repositories?per_page=100&page={page}"
            )
            if not isinstance(payload, dict):
                return repositories
            page_repositories = payload.get("repositories")
            if not isinstance(page_repositories, list):
                return repositories
            repositories.extend(item for item in page_repositories if isinstance(item, dict))
            if len(page_repositories) < 100:
                return repositories
            page += 1

    async def fetch_repository_languages(self, full_name: str) -> dict[str, int]:
        payload = await self._request_json(f"https://api.github.com/repos/{full_name}/languages")
        if not isinstance(payload, dict):
            return {}
        languages: dict[str, int] = {}
        for language, byte_count in payload.items():
            if isinstance(language, str) and isinstance(byte_count, int):
                languages[language] = byte_count
        return languages

    async def fetch_repository_commits_by_author(
        self,
        *,
        full_name: str,
        author_login: str,
    ) -> list[dict[str, Any]]:
        payload = await self._request_json(
            f"https://api.github.com/repos/{full_name}/commits?"
            + urlencode({"author": author_login, "per_page": "100"})
        )
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict)]

    async def search_user_pull_requests(self, *, author_login: str) -> list[dict[str, Any]]:
        return await self._search_issues(
            query=f"type:pr author:{author_login}",
        )

    async def search_user_merged_pull_requests(self, *, author_login: str) -> list[dict[str, Any]]:
        return await self._search_issues(
            query=f"type:pr author:{author_login} is:merged",
        )

    async def search_user_issues(self, *, author_login: str) -> list[dict[str, Any]]:
        return await self._search_issues(
            query=f"type:issue author:{author_login}",
        )

    async def _search_issues(self, *, query: str) -> list[dict[str, Any]]:
        payload = await self._request_json(
            "https://api.github.com/search/issues?"
            + urlencode(
                {
                    "q": query,
                    "sort": "updated",
                    "order": "desc",
                    "per_page": "100",
                }
            )
        )
        if not isinstance(payload, dict):
            return []
        items = payload.get("items")
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    async def _request_json(self, url: str):
        def _do_request():
            request = URLRequest(url=url, method="GET")
            request.add_header("Authorization", f"Bearer {self.access_token}")
            request.add_header("Accept", "application/vnd.github+json")
            request.add_header("X-GitHub-Api-Version", "2022-11-28")
            with urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8")

        try:
            raw = await asyncio.to_thread(_do_request)
            return json.loads(raw)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            logger.warning("GitHub API request failed (url=%s).", url)
            raise GitHubException(
                code=GitHubErrorCode.GITHUB_API_REQUEST_FAILED,
            ) from error


class GitHubAppClient:
    def __init__(self, *, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key

    @classmethod
    def from_settings(cls) -> "GitHubAppClient":
        app_id = SETTINGS.GITHUB_APP_ID.strip()
        private_key = SETTINGS.get_github_app_private_key()
        if not app_id or not private_key:
            raise GitHubException(
                code=GitHubErrorCode.GITHUB_APP_CONFIG_INVALID,
                details={
                    "missing": [
                        name
                        for name, value in {
                            "GITHUB_APP_ID": app_id,
                            "GITHUB_APP_PRIVATE_KEY_OR_PATH": private_key,
                        }.items()
                        if not value
                    ]
                },
            )
        return cls(app_id=app_id, private_key=private_key)

    async def create_installation_access_token(self, github_installation_id: int) -> str:
        app_jwt = self._create_app_jwt()
        payload = await self._request_json(
            f"https://api.github.com/app/installations/{github_installation_id}/access_tokens",
            app_jwt=app_jwt,
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("token"), str):
            raise GitHubException(code=GitHubErrorCode.GITHUB_API_REQUEST_FAILED)
        return str(payload["token"])

    def _create_app_jwt(self) -> str:
        now = int(datetime.now(UTC).timestamp())
        return jwt.encode(
            {
                "iat": now - 60,
                "exp": now + 9 * 60,
                "iss": self.app_id,
            },
            self.private_key,
            algorithm="RS256",
        )

    async def _request_json(self, url: str, *, app_jwt: str):
        def _do_request():
            request = URLRequest(url=url, data=b"{}", method="POST")
            request.add_header("Authorization", f"Bearer {app_jwt}")
            request.add_header("Accept", "application/vnd.github+json")
            request.add_header("Content-Type", "application/json")
            request.add_header("X-GitHub-Api-Version", "2022-11-28")
            with urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8")

        try:
            raw = await asyncio.to_thread(_do_request)
            return json.loads(raw)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            logger.warning("GitHub App API request failed (url=%s).", url)
            raise GitHubException(
                code=GitHubErrorCode.GITHUB_API_REQUEST_FAILED,
            ) from error


def _parse_github_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
