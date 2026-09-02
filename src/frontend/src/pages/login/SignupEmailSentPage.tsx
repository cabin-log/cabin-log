import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

import { InfoCard, WarningCard } from "../../components/ui/status/StatusCard";
import { Button, PanelCard } from "../../components/ui";
import { useAuthApi } from "../../hooks/api/auth/useAuthApi";
import { useAppConfig } from "../../hooks/useFeatures";

type SignupEmailSentLocationState = {
    email?: string;
};

export function SignupEmailSentPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { resendVerificationEmail } = useAuthApi();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const location = useLocation();
    const state = (location.state ?? {}) as SignupEmailSentLocationState;
    const email = state.email?.trim();
    const [resending, setResending] = useState(false);
    const [resendMessage, setResendMessage] = useState("");
    const emailEnabled = appConfig?.email_enabled === true;
    const showAccountCreated = !configLoading && !emailEnabled;

    const onResend = async () => {
        if (!email || resending || !emailEnabled) return;
        setResending(true);
        setResendMessage("");

        try {
            const payload = await resendVerificationEmail(email);
            setResendMessage(payload.message);
        } catch {
            setResendMessage(t("signupEmailSent.resendFallback"));
        } finally {
            setResending(false);
        }
    };

    return (
        <main className="page auth-page">
            <PanelCard
                className="auth-panel"
                title={
                    showAccountCreated
                        ? t("signupEmailSent.accountCreatedTitle")
                        : t("signupEmailSent.title")
                }
                subtitle={
                    showAccountCreated
                        ? t("signupEmailSent.accountCreatedSubtitle")
                        : t("signupEmailSent.subtitle", {
                              email: email || t("signupEmailSent.noEmail"),
                          })
                }
            >
                {showAccountCreated ? (
                    <InfoCard
                        title={t("cards.infoTitle")}
                        message={t("signupEmailSent.accountCreatedMessage")}
                    />
                ) : (
                    <>
                        <p className="muted signup-email-sent__description">
                            {t("signupEmailSent.description")}
                        </p>
                        {resendMessage ? (
                            <WarningCard title={t("cards.warningTitle")} message={resendMessage} />
                        ) : null}
                    </>
                )}
                <div className="auth-actions signup-email-sent__actions">
                    {!showAccountCreated ? (
                        <Button
                            type="button"
                            onClick={onResend}
                            loading={resending}
                            disabled={!email || configLoading || !emailEnabled}
                        >
                            {t("signupEmailSent.resendButton")}
                        </Button>
                    ) : null}
                    <Button type="button" onClick={() => navigate("/login", { replace: true })}>
                        {t("signupEmailSent.loginButton")}
                    </Button>
                </div>
            </PanelCard>
        </main>
    );
}
