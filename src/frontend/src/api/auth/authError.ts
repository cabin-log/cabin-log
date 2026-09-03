import type { TFunction } from "i18next";

import type { components } from "../generated/openapi";

type AuthErrorDetailSchema = components["schemas"]["AuthErrorDetail"];

export type AuthErrorCode = AuthErrorDetailSchema["error"];

const AUTH_ERROR_CODES = [
    "ACCOUNT_LOCKED",
    "EMAIL_ALREADY_EXISTS",
    "EMAIL_DISABLED",
    "EMAIL_NOT_VERIFIED",
    "LOGIN_DISABLED",
    "INVALID_CREDENTIALS",
    "INVALID_TOKEN",
    "INSUFFICIENT_ROLE",
    "OAUTH_IDENTITY_CONFLICT",
    "OAUTH_PROVIDER_CONFIG_INVALID",
    "OAUTH_PROVIDER_NOT_ENABLED",
    "OAUTH_PROVIDER_REQUEST_FAILED",
    "OAUTH_SIGNUP_FAILED",
    "PASSWORD_AUTH_DISABLED",
    "PROFILE_UPDATE_FAILED",
    "SIGNUP_FAILED",
    "USER_NOT_FOUND",
] as const satisfies readonly AuthErrorCode[];

const AUTH_ERROR_CODE_SET = new Set<AuthErrorCode>(AUTH_ERROR_CODES);

export type ApiErrorDetail = Partial<Pick<AuthErrorDetailSchema, "error" | "message">> & {
    details?: {
        remaining_attempts?: number;
        remaining_seconds?: number;
        [key: string]: unknown;
    } | null;
};

type ApiError = {
    detail?: AuthErrorDetailSchema | ApiErrorDetail;
};

const AUTH_ERROR_CODE_TO_KEY: Record<AuthErrorCode, string> = {
    ACCOUNT_LOCKED: "auth.errors.accountLocked",
    EMAIL_ALREADY_EXISTS: "auth.errors.emailAlreadyExists",
    EMAIL_DISABLED: "auth.errors.emailDisabled",
    EMAIL_NOT_VERIFIED: "auth.errors.emailNotVerified",
    LOGIN_DISABLED: "auth.errors.loginDisabled",
    INVALID_CREDENTIALS: "auth.errors.loginFallback",
    INVALID_TOKEN: "auth.errors.invalidToken",
    INSUFFICIENT_ROLE: "auth.errors.insufficientRole",
    USER_NOT_FOUND: "auth.errors.userNotFound",
    PROFILE_UPDATE_FAILED: "auth.errors.profileUpdateFailed",
    OAUTH_PROVIDER_NOT_ENABLED: "auth.errors.oauthProviderNotEnabled",
    OAUTH_PROVIDER_CONFIG_INVALID: "auth.errors.oauthProviderConfigInvalid",
    OAUTH_IDENTITY_CONFLICT: "auth.errors.oauthIdentityConflict",
    OAUTH_SIGNUP_FAILED: "auth.errors.oauthSignupFailed",
    OAUTH_PROVIDER_REQUEST_FAILED: "auth.errors.oauthProviderRequestFailed",
    PASSWORD_AUTH_DISABLED: "auth.errors.passwordAuthDisabled",
    SIGNUP_FAILED: "auth.errors.signupFallback",
};

function isAuthErrorCode(value: unknown): value is AuthErrorCode {
    return typeof value === "string" && AUTH_ERROR_CODE_SET.has(value as AuthErrorCode);
}

export function extractApiDetail(error: unknown): ApiErrorDetail | null {
    if (!error || typeof error !== "object") return null;
    const detail = (error as ApiError).detail;
    if (!detail || typeof detail !== "object") return null;

    const rawError = (detail as { error?: unknown }).error;
    const rawMessage = (detail as { message?: unknown }).message;
    const rawDetails = (detail as { details?: unknown }).details;

    const normalizedDetail: ApiErrorDetail = {
        error: isAuthErrorCode(rawError) ? rawError : undefined,
        message: typeof rawMessage === "string" ? rawMessage : undefined,
        details:
            rawDetails && typeof rawDetails === "object"
                ? (rawDetails as ApiErrorDetail["details"])
                : undefined,
    };

    return normalizedDetail;
}

export function resolveAuthErrorMessage(
    t: TFunction,
    detail: ApiErrorDetail | null,
    fallbackKey: string,
): string {
    const code = detail?.error;
    if (code) {
        const i18nKey = AUTH_ERROR_CODE_TO_KEY[code];
        if (i18nKey) {
            return t(i18nKey);
        }
    }

    return detail?.message || detail?.error || t(fallbackKey);
}
