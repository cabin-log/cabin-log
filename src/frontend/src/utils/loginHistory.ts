const RECENT_LOGIN_ACCOUNT_KEY = "cabinlog:login:v1:recent-account";

export type LoginHistoryUser = {
    id: number;
    email: string;
    name: string;
    profile_image_url?: string | null;
    oauth_providers?: string[];
};

export type RecentLoginAccount = {
    userId: number;
    email: string;
    name: string;
    profileImageUrl: string | null;
    provider: "github";
    updatedAt: string;
};

function isRecentLoginAccount(value: unknown): value is RecentLoginAccount {
    if (!value || typeof value !== "object") {
        return false;
    }

    const candidate = value as Partial<RecentLoginAccount>;
    return (
        typeof candidate.userId === "number" &&
        typeof candidate.email === "string" &&
        typeof candidate.name === "string" &&
        (typeof candidate.profileImageUrl === "string" || candidate.profileImageUrl === null) &&
        candidate.provider === "github" &&
        typeof candidate.updatedAt === "string"
    );
}

export function toRecentLoginAccount(user: LoginHistoryUser | null): RecentLoginAccount | null {
    if (!user?.oauth_providers?.includes("github")) {
        return null;
    }

    return {
        userId: user.id,
        email: user.email,
        name: user.name,
        profileImageUrl: user.profile_image_url ?? null,
        provider: "github",
        updatedAt: new Date().toISOString(),
    };
}

export function getRecentLoginAccount(): RecentLoginAccount | null {
    try {
        const rawValue = window.localStorage.getItem(RECENT_LOGIN_ACCOUNT_KEY);
        if (!rawValue) {
            return null;
        }

        const parsedValue: unknown = JSON.parse(rawValue);
        return isRecentLoginAccount(parsedValue) ? parsedValue : null;
    } catch {
        return null;
    }
}

export function rememberRecentLoginAccount(
    user: LoginHistoryUser | null,
): RecentLoginAccount | null {
    const recentAccount = toRecentLoginAccount(user);
    if (!recentAccount) {
        return null;
    }

    try {
        window.localStorage.setItem(RECENT_LOGIN_ACCOUNT_KEY, JSON.stringify(recentAccount));
    } catch {
        // ignore storage errors in restricted browser contexts
    }

    return recentAccount;
}
