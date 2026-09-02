import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";

import type { User } from "../api/auth/authApi";
import type { AppConfig } from "../api/config/configApi";
import { useAuthApi } from "./api/auth/useAuthApi";
import { useConfigApi } from "./api/config/useConfigApi";
import { clearAccessToken, getAccessToken, setAccessToken } from "../store/session";
import { rememberRecentLoginAccount } from "../utils/loginHistory";

type AuthContextValue = {
    user: RoleAwareUser | null;
    loading: boolean;
    login: (input: { email: string; password: string; remember_me: boolean }) => Promise<void>;
    signup: (input: { email: string; name: string; password: string }) => Promise<void>;
    updateProfile: (input: { name?: string; profile_image_url?: string | null }) => Promise<void>;
    logout: () => Promise<void>;
    refreshSession: () => Promise<void>;
    revalidateSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

type RoleAwareUser = User & { role?: "admin" | "user" };

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const { getConfig } = useConfigApi();
    const {
        refresh: refreshAuth,
        me,
        login: loginAuth,
        signup: signupAuth,
        updateMe,
        logout: logoutAuth,
    } = useAuthApi();
    const [user, setUser] = useState<RoleAwareUser | null>(null);
    const [loading, setLoading] = useState(true);
    const refreshInFlightRef = useRef<Promise<void> | null>(null);

    const refreshSession = useCallback(async () => {
        if (refreshInFlightRef.current) {
            return refreshInFlightRef.current;
        }

        const refreshTask = (async () => {
            const refreshResult = await refreshAuth();
            setAccessToken(refreshResult.access_token);
            const nextUser = await me();
            setUser(nextUser);
            rememberRecentLoginAccount(nextUser);
        })();

        refreshInFlightRef.current = refreshTask;
        try {
            await refreshTask;
        } finally {
            refreshInFlightRef.current = null;
        }
    }, [me, refreshAuth]);

    const revalidateSession = useCallback(async () => {
        try {
            const config = (await getConfig()) as AppConfig | undefined;
            if (config?.login_enabled === false) {
                if (config.bootstrap_access_token) {
                    setAccessToken(config.bootstrap_access_token);
                } else {
                    clearAccessToken();
                }
                const nextUser = config.bootstrap_user ?? null;
                setUser(nextUser);
                rememberRecentLoginAccount(nextUser);
                return;
            }

            const token = getAccessToken();
            if (token) {
                try {
                    const nextUser = await me();
                    setUser(nextUser);
                    rememberRecentLoginAccount(nextUser);
                    return;
                } catch {
                    clearAccessToken();
                }
            }

            await refreshSession();
        } catch {
            clearAccessToken();
            setUser(null);
        }
    }, [getConfig, me, refreshSession]);

    useEffect(() => {
        // Agent customization note:
        // This bootstrap flow is the single place to plug SSO/session policies.
        const bootstrap = async () => {
            try {
                await revalidateSession();
            } finally {
                setLoading(false);
            }
        };

        void bootstrap();
    }, [revalidateSession]);

    const value = useMemo<AuthContextValue>(
        () => ({
            user,
            loading,
            login: async (input) => {
                const payload = await loginAuth(input);
                setAccessToken(payload.access_token);
                setUser(payload.user);
                rememberRecentLoginAccount(payload.user);
            },
            signup: async (input) => {
                await signupAuth(input);
            },
            updateProfile: async (input) => {
                const nextUser = await updateMe(input);
                setUser(nextUser);
                rememberRecentLoginAccount(nextUser);
            },
            logout: async () => {
                try {
                    await logoutAuth();
                } finally {
                    clearAccessToken();
                    setUser(null);
                }
            },
            refreshSession,
            revalidateSession,
        }),
        [
            loading,
            loginAuth,
            logoutAuth,
            refreshSession,
            revalidateSession,
            signupAuth,
            updateMe,
            user,
        ],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuthContext must be used inside <AuthProvider>.");
    }
    return context;
}
