import type { TFunction } from "i18next";

import type { components } from "../generated/openapi";

type GameErrorDetailSchema = components["schemas"]["GameErrorDetail"];

export type GameErrorCode = GameErrorDetailSchema["error"];

const GAME_ERROR_CODES = [
    "REWARD_PACKAGE_NOT_FOUND",
    "REWARD_PACKAGE_ALREADY_CLAIMED",
    "CABIN_PLACEMENT_NOT_FOUND",
    "CABIN_PLACEMENT_INVALID",
    "CABIN_PLACEMENT_CONFLICT",
    "CABIN_ITEM_NOT_OWNED",
    "CABIN_SYSTEM_PLACEMENT_LOCKED",
] as const satisfies readonly GameErrorCode[];

const GAME_ERROR_CODE_SET = new Set<GameErrorCode>(GAME_ERROR_CODES);

type ApiError = {
    detail?: GameErrorDetailSchema | { error?: unknown; message?: unknown; details?: unknown };
};

const GAME_ERROR_CODE_TO_KEY: Record<GameErrorCode, string> = {
    REWARD_PACKAGE_NOT_FOUND: "game.errors.rewardPackageNotFound",
    REWARD_PACKAGE_ALREADY_CLAIMED: "game.errors.rewardPackageAlreadyClaimed",
    CABIN_PLACEMENT_NOT_FOUND: "game.errors.cabinPlacementNotFound",
    CABIN_PLACEMENT_INVALID: "game.errors.cabinPlacementInvalid",
    CABIN_PLACEMENT_CONFLICT: "game.errors.cabinPlacementConflict",
    CABIN_ITEM_NOT_OWNED: "game.errors.cabinItemNotOwned",
    CABIN_SYSTEM_PLACEMENT_LOCKED: "game.errors.cabinSystemPlacementLocked",
};

export type GameErrorDetail = Partial<Pick<GameErrorDetailSchema, "error" | "message">> & {
    details?: Record<string, unknown> | null;
};

function isGameErrorCode(value: unknown): value is GameErrorCode {
    return typeof value === "string" && GAME_ERROR_CODE_SET.has(value as GameErrorCode);
}

export function extractGameErrorDetail(error: unknown): GameErrorDetail | null {
    if (!error || typeof error !== "object") return null;
    const detail = (error as ApiError).detail;
    if (!detail || typeof detail !== "object") return null;

    const rawError = (detail as { error?: unknown }).error;
    const rawMessage = (detail as { message?: unknown }).message;
    const rawDetails = (detail as { details?: unknown }).details;

    return {
        error: isGameErrorCode(rawError) ? rawError : undefined,
        message: typeof rawMessage === "string" ? rawMessage : undefined,
        details:
            rawDetails && typeof rawDetails === "object"
                ? (rawDetails as GameErrorDetail["details"])
                : undefined,
    };
}

export function resolveGameErrorMessage(
    t: TFunction,
    detail: GameErrorDetail | null,
    fallbackKey: string,
): string {
    const code = detail?.error;
    if (code) {
        const i18nKey = GAME_ERROR_CODE_TO_KEY[code];
        if (i18nKey) {
            return t(i18nKey);
        }
    }

    return detail?.message || detail?.error || t(fallbackKey);
}
