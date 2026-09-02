import { ArrowRight, Github } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { BrandMark, PanelCard, UserAvatar } from "../../components/ui";
import { useAuthContext } from "../../hooks/useAuth";

export function LoginSuccessPage() {
    const { t } = useTranslation();
    const { user } = useAuthContext();
    const displayName = user?.name?.trim() || user?.email || t("loginSuccess.unknownUser");
    const avatarLabel = displayName.slice(0, 1).toUpperCase();
    const githubConnected = user?.oauth_providers?.includes("github") ?? false;

    return (
        <main className="page auth-page">
            <div className="auth-panel-stack auth-panel-stack--github-only">
                <BrandMark className="brand-mark--login" />
                <PanelCard
                    className="auth-panel auth-panel--github-only login-success-panel"
                    title={t("loginSuccess.title")}
                    subtitle={t("loginSuccess.subtitle")}
                >
                    <div className="login-success-profile">
                        <UserAvatar
                            className="login-success-profile__avatar"
                            imageUrl={user?.profile_image_url}
                            label={avatarLabel}
                        />
                        <div>
                            <p className="login-success-profile__name">{displayName}</p>
                            <p className="login-success-profile__email">{user?.email}</p>
                        </div>
                    </div>
                    <div className="login-success-provider">
                        <Github aria-hidden="true" />
                        <span>
                            {githubConnected
                                ? t("loginSuccess.githubConnected")
                                : t("loginSuccess.sessionConnected")}
                        </span>
                    </div>
                    <Link to="/show-case" className="ui-button login-success-continue">
                        <span className="ui-button__content">
                            <span>{t("loginSuccess.continue")}</span>
                            <ArrowRight aria-hidden="true" />
                        </span>
                    </Link>
                </PanelCard>
            </div>
        </main>
    );
}
