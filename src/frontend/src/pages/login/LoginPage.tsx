import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Github } from "lucide-react";

import { OAuthProviderButton } from "../../components/features/auth/OAuthProviderButton";
import { InlineMessage, PanelCard, UserAvatar } from "../../components/ui";
import { useAuthApi, type OAuthProvider } from "../../hooks/api/auth/useAuthApi";
import { useAuthContext } from "../../hooks/useAuth";
import { useAppConfig } from "../../hooks/useFeatures";
import {
    getRecentLoginAccount,
    toRecentLoginAccount,
    type RecentLoginAccount,
} from "../../utils/loginHistory";
import { getApiBase } from "../../utils/apiBase";
import { markCabinEntryReveal } from "../../utils/cabinEntryReveal";

export function LoginPage() {
    const { t } = useTranslation();
    const { getOAuthProviders } = useAuthApi();
    const { user, loading: authLoading } = useAuthContext();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const [oauthProviders, setOAuthProviders] = useState<
        Array<{ provider: OAuthProvider; start_path: string }>
    >([]);
    const [oauthLoading, setOAuthLoading] = useState(false);
    const [oauthLoadFailed, setOAuthLoadFailed] = useState(false);
    const [isEnteringCabin, setIsEnteringCabin] = useState(false);
    const [recentAccount, setRecentAccount] = useState<RecentLoginAccount | null>(() =>
        getRecentLoginAccount(),
    );
    const oauthRedirectTimerRef = useRef<number | null>(null);
    const loginEnabled = appConfig?.login_enabled === true;
    const oauthEnabled = appConfig?.oauth_enabled === true;
    const githubProvider = oauthProviders.find((item) => item.provider === "github");
    const activeGithubAccount = toRecentLoginAccount(user);
    const accountShortcut = activeGithubAccount ?? recentAccount;

    useEffect(() => {
        const run = async () => {
            if (!oauthEnabled || !loginEnabled) {
                setOAuthProviders([]);
                setOAuthLoading(false);
                return;
            }
            setOAuthLoading(true);
            try {
                const payload = await getOAuthProviders();
                setOAuthProviders(payload.providers.filter((item) => item.provider === "github"));
                setOAuthLoadFailed(false);
            } catch {
                setOAuthProviders([]);
                setOAuthLoadFailed(true);
            } finally {
                setOAuthLoading(false);
            }
        };
        void run();
    }, [getOAuthProviders, oauthEnabled, loginEnabled]);

    useEffect(() => {
        const clearOauthRedirectTimer = () => {
            if (oauthRedirectTimerRef.current !== null) {
                window.clearTimeout(oauthRedirectTimerRef.current);
                oauthRedirectTimerRef.current = null;
            }
        };

        const resetRestoredEntryState = (event: PageTransitionEvent) => {
            if (event.persisted) {
                clearOauthRedirectTimer();
                setIsEnteringCabin(false);
            }
        };

        window.addEventListener("pageshow", resetRestoredEntryState);
        return () => {
            window.removeEventListener("pageshow", resetRestoredEntryState);
            clearOauthRedirectTimer();
        };
    }, []);

    useEffect(() => {
        if (activeGithubAccount) {
            setRecentAccount(activeGithubAccount);
        }
    }, [activeGithubAccount]);

    const beginCabinEntry = (oauthStartUrl: string) => {
        if (isEnteringCabin) {
            return false;
        }
        setIsEnteringCabin(true);
        markCabinEntryReveal();
        oauthRedirectTimerRef.current = window.setTimeout(() => {
            window.location.assign(oauthStartUrl);
        }, 1150);
        return false;
    };

    const startRecentAccount = () => {
        if (isEnteringCabin) {
            return;
        }

        setIsEnteringCabin(true);
        markCabinEntryReveal();
        oauthRedirectTimerRef.current = window.setTimeout(() => {
            if (githubProvider) {
                const oauthStartUrl = new URL(
                    githubProvider.start_path,
                    `${getApiBase()}/`,
                ).toString();
                window.location.assign(oauthStartUrl);
            }
        }, 1150);
    };

    let message: string | null = null;
    if (!configLoading && !loginEnabled) {
        message = t("auth.errors.loginDisabled");
    } else if (oauthLoadFailed) {
        message = t("auth.errors.oauthProviderRequestFailed");
    } else if (!configLoading && !oauthLoading && (!oauthEnabled || !githubProvider)) {
        message = t("login.githubUnavailable");
    }

    return (
        <main
            className={`page auth-page auth-page--init${isEnteringCabin ? " auth-page--entering-cabin" : ""}`}
        >
            <div className="auth-panel-stack auth-panel-stack--github-only">
                <img
                    className="auth-title-image"
                    src="/sprites/img/title.png"
                    alt="Cabin Log"
                    draggable="false"
                />
                <PanelCard className="auth-panel auth-panel--github-only">
                    {message ? <InlineMessage>{message}</InlineMessage> : null}
                    {configLoading || oauthLoading ? (
                        <InlineMessage tone="info">{t("login.loadingGithub")}</InlineMessage>
                    ) : null}
                    {loginEnabled && accountShortcut && githubProvider ? (
                        <button
                            type="button"
                            className="auth-recent-account-button"
                            disabled={isEnteringCabin || authLoading}
                            onClick={startRecentAccount}
                            aria-label={t("login.recentAccount.startAria", {
                                name: accountShortcut.name,
                            })}
                        >
                            <UserAvatar
                                className="auth-recent-account-button__avatar"
                                imageUrl={accountShortcut.profileImageUrl}
                                label={accountShortcut.name || accountShortcut.email}
                            />
                            <span className="auth-recent-account-button__body">
                                <span className="auth-recent-account-button__name">
                                    {accountShortcut.name}
                                </span>
                                <span className="auth-recent-account-button__email">
                                    {accountShortcut.email}
                                </span>
                            </span>
                        </button>
                    ) : null}
                    {loginEnabled && githubProvider ? (
                        <div className="oauth-provider-list oauth-provider-list--icon-only">
                            <OAuthProviderButton
                                provider="github"
                                label={t(
                                    accountShortcut
                                        ? "login.oauth.providers.githubDifferent"
                                        : "login.oauth.providers.github",
                                )}
                                startPath={githubProvider.start_path}
                                disabled={isEnteringCabin}
                                onBeforeNavigate={beginCabinEntry}
                                prompt={accountShortcut ? "select_account" : undefined}
                            />
                        </div>
                    ) : null}
                </PanelCard>
            </div>
            <a
                className="auth-github-link"
                href="https://github.com/cabin-log/cabin-log"
                target="_blank"
                rel="noreferrer"
                aria-label="Open Cabinlog GitHub repository"
            >
                <Github aria-hidden="true" />
                <span>GitHub</span>
            </a>
        </main>
    );
}
