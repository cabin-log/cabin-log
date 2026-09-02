from urllib.parse import urlencode, urljoin

from fastapi import APIRouter, Body, Depends, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config.settings import SETTINGS
from app.core.error import AuthErrorCode, AuthException, auth_error_responses
from app.core.observability.logging import get_logger
from app.deps import get_current_admin_user, get_current_user
from app.models.github import GitHubProfiles
from app.models.oauth import OAuthProvider, OAuthProvidersResponse
from app.models.user import (
    ForgotPasswordForm,
    ForgotPasswordResponse,
    LoginForm,
    LoginResponse,
    RefreshResponse,
    ResendVerificationForm,
    ResendVerificationResponse,
    ResetPasswordForm,
    ResetPasswordResponse,
    SignupForm,
    UpdateProfileForm,
    UserResponse,
    UserRoleStatsResponse,
    VerifyEmailForm,
    VerifyEmailResponse,
)
from app.services.auth import AuthService
from app.utils.cookies import clear_refresh_cookies, set_refresh_cookies
from app.utils.token import create_refresh_session_id

router = APIRouter()
logger = get_logger("app.router.auth")


def _resolve_preferred_language(request: Request) -> str | None:
    app_language = request.headers.get("X-App-Language")
    if app_language and app_language.strip():
        return app_language
    return request.headers.get("Accept-Language")


def _oauth_json_mode_enabled() -> bool:
    return SETTINGS.OAUTH_CALLBACK_RESPONSE_MODE == "json"


def _oauth_failure_response(error: str, message: str | None = None) -> Response:
    if _oauth_json_mode_enabled():
        payload: dict[str, str] = {"error": error}
        if message:
            payload["message"] = message
        return JSONResponse(status_code=400, content=payload)

    failure_query = urlencode(
        {"error": error} if message is None else {"error": error, "message": message}
    )
    failure_url = urljoin(
        f"{SETTINGS.APP_BASE_URL.rstrip('/')}/",
        SETTINGS.OAUTH_FRONTEND_FAILURE_PATH.lstrip("/"),
    )
    return RedirectResponse(url=f"{failure_url}?{failure_query}", status_code=307)


@router.post(
    "/signup",
    response_model=UserResponse,
    responses=auth_error_responses(
        AuthErrorCode.EMAIL_ALREADY_EXISTS,
        AuthErrorCode.SIGNUP_FAILED,
        AuthErrorCode.PASSWORD_AUTH_DISABLED,
    ),
)
async def signup(
    request: Request,
    form: SignupForm,
    service: AuthService = Depends(AuthService),
) -> UserResponse:
    return await service.signup(form, preferred_language=_resolve_preferred_language(request))


@router.get(
    "/oauth/providers",
    response_model=OAuthProvidersResponse,
    responses=auth_error_responses(
        AuthErrorCode.LOGIN_DISABLED,
        AuthErrorCode.OAUTH_PROVIDER_NOT_ENABLED,
        AuthErrorCode.OAUTH_PROVIDER_CONFIG_INVALID,
    ),
)
async def oauth_providers(service: AuthService = Depends(AuthService)) -> OAuthProvidersResponse:
    providers = service.get_oauth_provider_public_configs()
    logger.debug("OAuth providers fetched (count=%s).", len(providers))
    return OAuthProvidersResponse(providers=providers)


@router.get(
    "/oauth/{provider}/start",
    responses=auth_error_responses(
        AuthErrorCode.LOGIN_DISABLED,
        AuthErrorCode.OAUTH_PROVIDER_NOT_ENABLED,
        AuthErrorCode.OAUTH_PROVIDER_CONFIG_INVALID,
    ),
)
async def oauth_start(
    provider: OAuthProvider,
    request: Request,
    prompt: str | None = Query(default=None),
    service: AuthService = Depends(AuthService),
) -> RedirectResponse:
    redirect_uri = str(request.url_for("oauth_callback", provider=provider.value))
    authorization_url = await service.build_oauth_authorization_url(
        provider,
        redirect_uri,
        prompt=prompt,
    )
    return RedirectResponse(url=authorization_url, status_code=307)


@router.get(
    "/oauth/{provider}/callback",
    name="oauth_callback",
)
async def oauth_callback(
    provider: OAuthProvider,
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    service: AuthService = Depends(AuthService),
) -> Response:
    # Provider-side errors are returned as a frontend redirect, not raised as API JSON errors.
    if error:
        logger.error(
            "OAuth callback returned provider error (provider=%s, error=%s).", provider, error
        )
        return _oauth_failure_response(error=error)

    # OAuth callback contract requires both authorization code and state.
    try:
        code_value, state_value = service.require_oauth_callback_params(
            provider=provider,
            code=code,
            state=state,
        )
    except AuthException as callback_error:
        logger.error(
            "OAuth callback missing required params (provider=%s, code=%s).",
            provider.value,
            callback_error.code.error,
        )
        return _oauth_failure_response(
            error=callback_error.code.error,
            message=callback_error.message,
        )

    refresh_session_id = create_refresh_session_id()
    try:
        token_payload = await service.oauth_callback_login(
            provider=provider,
            code=code_value,
            state=state_value,
            redirect_uri=str(request.url_for("oauth_callback", provider=provider.value)),
            request=request,
            refresh_session_id=refresh_session_id,
        )
    except AuthException as auth_error:
        # Domain failures are propagated to frontend with code/message query parameters.
        logger.error(
            "OAuth callback login failed (provider=%s, code=%s).",
            provider.value,
            auth_error.code.error,
        )
        return _oauth_failure_response(error=auth_error.code.error, message=auth_error.message)

    if _oauth_json_mode_enabled():
        github_profile = None
        if provider == OAuthProvider.GITHUB:
            github_profile = await GitHubProfiles.get_profile_by_user_id(token_payload.user.id)

        response = JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {
                    **token_payload.model_dump(),
                    "github_profile": github_profile,
                }
            ),
        )
        set_refresh_cookies(
            response=response,
            request=request,
            refresh_token=token_payload.refresh_token,
            refresh_session_id=refresh_session_id,
            remember_me=True,
        )
        return response

    success_url = urljoin(
        f"{SETTINGS.APP_BASE_URL.rstrip('/')}/",
        SETTINGS.OAUTH_FRONTEND_SUCCESS_PATH.lstrip("/"),
    )
    response = RedirectResponse(url=success_url, status_code=307)
    set_refresh_cookies(
        response=response,
        request=request,
        refresh_token=token_payload.refresh_token,
        refresh_session_id=refresh_session_id,
        remember_me=True,
    )
    return response


@router.post(
    "/token",
    response_model=LoginResponse,
    responses=auth_error_responses(
        AuthErrorCode.LOGIN_DISABLED,
        AuthErrorCode.PASSWORD_AUTH_DISABLED,
        AuthErrorCode.INVALID_CREDENTIALS,
        AuthErrorCode.EMAIL_NOT_VERIFIED,
        AuthErrorCode.ACCOUNT_LOCKED,
    ),
)
async def oauth_token_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(AuthService),
) -> LoginResponse:
    refresh_session_id = create_refresh_session_id()
    form = LoginForm(
        email=form_data.username,
        password=form_data.password,
        remember_me=False,
    )
    return await service.login(form, request, refresh_session_id=refresh_session_id)


@router.post(
    "/login",
    response_model=LoginResponse,
    responses=auth_error_responses(
        AuthErrorCode.LOGIN_DISABLED,
        AuthErrorCode.PASSWORD_AUTH_DISABLED,
        AuthErrorCode.INVALID_CREDENTIALS,
        AuthErrorCode.EMAIL_NOT_VERIFIED,
        AuthErrorCode.ACCOUNT_LOCKED,
    ),
)
async def login(
    request: Request,
    response: Response,
    form: LoginForm,
    service: AuthService = Depends(AuthService),
) -> LoginResponse:
    refresh_session_id = create_refresh_session_id()
    token_payload = await service.login(form, request, refresh_session_id=refresh_session_id)

    set_refresh_cookies(
        response=response,
        request=request,
        refresh_token=token_payload.refresh_token,
        refresh_session_id=refresh_session_id,
        remember_me=form.remember_me,
    )
    return token_payload


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user


@router.get(
    "/admin/user-role-stats",
    response_model=UserRoleStatsResponse,
    responses=auth_error_responses(
        AuthErrorCode.INVALID_TOKEN,
        AuthErrorCode.INSUFFICIENT_ROLE,
    ),
)
async def admin_user_role_stats(
    _current_admin_user: UserResponse = Depends(get_current_admin_user),
    service: AuthService = Depends(AuthService),
) -> UserRoleStatsResponse:
    return await service.get_admin_user_role_stats()


@router.patch(
    "/me",
    response_model=UserResponse,
    responses=auth_error_responses(AuthErrorCode.PROFILE_UPDATE_FAILED),
)
async def update_me(
    form: UpdateProfileForm,
    current_user: UserResponse = Depends(get_current_user),
    service: AuthService = Depends(AuthService),
) -> UserResponse:
    return await service.update_profile(user_id=current_user.id, form=form)


@router.post("/logout")
async def logout(
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
    service: AuthService = Depends(AuthService),
) -> dict[str, str]:
    await service.logout(current_user.id)
    clear_refresh_cookies(response)
    return {"message": "Successfully logged out."}


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    responses=auth_error_responses(
        AuthErrorCode.INVALID_TOKEN,
        AuthErrorCode.USER_NOT_FOUND,
    ),
)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Body(default=None, embed=True),
    user_id: int | None = Body(default=None, embed=True),
    session_id: str | None = Body(default=None, embed=True),
    service: AuthService = Depends(AuthService),
) -> RefreshResponse:
    try:
        token_payload, session_id_value, remember_me = await service.refresh_with_request_context(
            request=request,
            refresh_token=refresh_token,
            user_id=user_id,
            session_id=session_id,
        )
    except AuthException:
        clear_refresh_cookies(response)
        raise

    set_refresh_cookies(
        response=response,
        request=request,
        refresh_token=token_payload.refresh_token,
        refresh_session_id=session_id_value,
        remember_me=remember_me,
    )
    return token_payload


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    responses=auth_error_responses(
        AuthErrorCode.INVALID_TOKEN,
        AuthErrorCode.USER_NOT_FOUND,
        AuthErrorCode.PASSWORD_AUTH_DISABLED,
    ),
)
async def verify_email(
    form: VerifyEmailForm,
    service: AuthService = Depends(AuthService),
) -> VerifyEmailResponse:
    user = await service.verify_email(form.token)
    return VerifyEmailResponse(message="Email verified successfully.", user=user)


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    responses=auth_error_responses(AuthErrorCode.PASSWORD_AUTH_DISABLED),
)
async def resend_verification_email(
    request: Request,
    form: ResendVerificationForm,
    service: AuthService = Depends(AuthService),
) -> ResendVerificationResponse:
    await service.resend_verification_email(
        form.email,
        preferred_language=_resolve_preferred_language(request),
    )
    return ResendVerificationResponse(
        message="If an unverified account exists, a verification email has been sent.",
    )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    responses=auth_error_responses(
        AuthErrorCode.PASSWORD_AUTH_DISABLED,
        AuthErrorCode.EMAIL_DISABLED,
    ),
)
async def forgot_password(
    request: Request,
    form: ForgotPasswordForm,
    service: AuthService = Depends(AuthService),
) -> ForgotPasswordResponse:
    await service.request_password_reset(
        form.email,
        preferred_language=_resolve_preferred_language(request),
    )
    return ForgotPasswordResponse(
        message="If the account exists, a password reset email has been sent.",
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    responses=auth_error_responses(
        AuthErrorCode.INVALID_TOKEN,
        AuthErrorCode.PASSWORD_AUTH_DISABLED,
        AuthErrorCode.EMAIL_DISABLED,
        AuthErrorCode.USER_NOT_FOUND,
    ),
)
async def reset_password(
    form: ResetPasswordForm,
    service: AuthService = Depends(AuthService),
) -> ResetPasswordResponse:
    await service.reset_password(form.token, form.password)
    return ResetPasswordResponse(message="Password reset completed successfully.")
