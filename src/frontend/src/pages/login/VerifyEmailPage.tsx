import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

import { ErrorCard } from "../../components/ui/status/StatusCard";
import { Button, PanelCard } from "../../components/ui";
import { useAuthApi } from "../../hooks/api/auth/useAuthApi";

type VerifyStatus = "loading" | "success" | "error";

export function VerifyEmailPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { verifyEmail, extractApiDetail, resolveAuthErrorMessage } = useAuthApi();
    const location = useLocation();
    const [status, setStatus] = useState<VerifyStatus>("loading");
    const [errorMessage, setErrorMessage] = useState("");

    const token = useMemo(() => {
        const params = new URLSearchParams(location.search);
        return (params.get("token") || "").trim();
    }, [location.search]);

    useEffect(() => {
        const run = async () => {
            if (!token) {
                setStatus("error");
                setErrorMessage(t("verifyEmail.errors.missingToken"));
                return;
            }

            try {
                await verifyEmail(token);
                setStatus("success");
            } catch (nextError) {
                const detail = extractApiDetail(nextError);
                setStatus("error");
                setErrorMessage(resolveAuthErrorMessage(t, detail, "verifyEmail.errors.fallback"));
            }
        };

        void run();
    }, [token, t]);

    if (status === "loading") {
        return (
            <main className="page auth-page">
                <PanelCard
                    className="auth-panel"
                    title={t("verifyEmail.loadingTitle")}
                    subtitle={t("verifyEmail.loadingSubtitle")}
                >
                    <p className="muted">{t("verifyEmail.loadingDescription")}</p>
                </PanelCard>
            </main>
        );
    }

    if (status === "error") {
        return (
            <main className="page auth-page">
                <PanelCard
                    className="auth-panel"
                    title={t("verifyEmail.errorTitle")}
                    subtitle={t("verifyEmail.errorSubtitle")}
                >
                    <ErrorCard
                        title={t("cards.errorTitle")}
                        message={errorMessage || t("verifyEmail.errors.fallback")}
                    />
                    <div className="verify-email__actions">
                        <Button type="button" onClick={() => navigate("/login", { replace: true })}>
                            {t("verifyEmail.backToLogin")}
                        </Button>
                    </div>
                </PanelCard>
            </main>
        );
    }

    return (
        <main className="page auth-page">
            <PanelCard
                className="auth-panel"
                title={t("verifyEmail.successTitle")}
                subtitle={t("verifyEmail.successSubtitle")}
            >
                <p className="muted">{t("verifyEmail.successDescription")}</p>
                <div className="verify-email__actions">
                    <Button type="button" onClick={() => navigate("/login", { replace: true })}>
                        {t("verifyEmail.backToLogin")}
                    </Button>
                </div>
            </PanelCard>
        </main>
    );
}
