import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Github } from "lucide-react";

import { OAuthProviderButton } from "../../components/features/auth/OAuthProviderButton";
import { InlineMessage, PanelCard } from "../../components/ui";
import { useAuthApi, type OAuthProvider } from "../../hooks/api/auth/useAuthApi";
import { useAppConfig } from "../../hooks/useFeatures";

export function LoginPage() {
    const { t } = useTranslation();
    const { getOAuthProviders } = useAuthApi();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const [oauthProviders, setOAuthProviders] = useState<
        Array<{ provider: OAuthProvider; start_path: string }>
    >([]);
    const [oauthLoading, setOAuthLoading] = useState(false);
    const [oauthLoadFailed, setOAuthLoadFailed] = useState(false);
    const loginEnabled = appConfig?.login_enabled === true;
    const oauthEnabled = appConfig?.oauth_enabled === true;
    const githubProvider = oauthProviders.find((item) => item.provider === "github");

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

    let message: string | null = null;
    if (!configLoading && !loginEnabled) {
        message = t("auth.errors.loginDisabled");
    } else if (oauthLoadFailed) {
        message = t("auth.errors.oauthProviderRequestFailed");
    } else if (!configLoading && !oauthLoading && (!oauthEnabled || !githubProvider)) {
        message = t("login.githubUnavailable");
    }

    return (
        <main className="page auth-page">
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
                    {loginEnabled && githubProvider ? (
                        <div className="oauth-provider-list oauth-provider-list--icon-only">
                            <OAuthProviderButton
                                provider="github"
                                label={t("login.oauth.providers.github")}
                                startPath={githubProvider.start_path}
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
