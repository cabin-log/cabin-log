import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

import { Button, PanelCard } from "../../components/ui";
import { InfoCard, WarningCard } from "../../components/ui/status/StatusCard";
import { useAppConfig } from "../../hooks/useFeatures";

type ForgotPasswordSentState = {
    email?: string;
};

export function ForgotPasswordEmailSentPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const location = useLocation();
    const state = (location.state ?? {}) as ForgotPasswordSentState;
    const email = state.email?.trim();
    const emailEnabled = appConfig?.email_enabled === true;
    const showDisabled = !configLoading && !emailEnabled;

    return (
        <main className="page auth-page">
            <PanelCard
                className="auth-panel"
                title={
                    showDisabled ? t("forgotPassword.disabledTitle") : t("forgotPassword.sentTitle")
                }
                subtitle={
                    showDisabled
                        ? t("forgotPassword.disabled")
                        : t("forgotPassword.sentSubtitle", {
                              email: email || t("forgotPassword.noEmail"),
                          })
                }
            >
                {showDisabled ? (
                    <WarningCard
                        title={t("cards.warningTitle")}
                        message={t("forgotPassword.disabled")}
                    />
                ) : (
                    <InfoCard
                        title={t("cards.infoTitle")}
                        message={t("forgotPassword.sentDescription")}
                    />
                )}
                <div className="auth-actions signup-email-sent__actions">
                    {!showDisabled ? (
                        <Button
                            type="button"
                            onClick={() => navigate("/forgot-password", { replace: true })}
                        >
                            {t("forgotPassword.backToRequest")}
                        </Button>
                    ) : null}
                    <Button type="button" onClick={() => navigate("/login", { replace: true })}>
                        {t("forgotPassword.backToLogin")}
                    </Button>
                </div>
            </PanelCard>
        </main>
    );
}
