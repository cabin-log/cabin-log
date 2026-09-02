import { FormEvent, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { ErrorCard, WarningCard } from "../../components/ui/status/StatusCard";
import {
    Button,
    InputField,
    PanelCard,
    ValidationCard,
    type ValidationRule,
} from "../../components/ui";
import { useAuthApi } from "../../hooks/api/auth/useAuthApi";
import { useAppConfig } from "../../hooks/useFeatures";
import { isValidPassword } from "../../utils/validation";

export function ResetPasswordPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { resetPassword, extractApiDetail, resolveAuthErrorMessage } = useAuthApi();
    const location = useLocation();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [warningMessage, setWarningMessage] = useState("");
    const emailEnabled = appConfig?.email_enabled === true;
    const passwordMismatch = confirmPassword.length > 0 && confirmPassword !== password;

    const token = useMemo(() => {
        const params = new URLSearchParams(location.search);
        return (params.get("token") || "").trim();
    }, [location.search]);

    const passwordRules = useMemo<ValidationRule[]>(
        () => [
            {
                label: t("signup.rules.password.length"),
                isValid: password.length >= 8 && password.length <= 24,
            },
            {
                label: t("signup.rules.password.upper"),
                isValid: /[A-Z]/.test(password),
            },
            {
                label: t("signup.rules.password.number"),
                isValid: /\d/.test(password),
            },
            {
                label: t("signup.rules.password.symbol"),
                isValid: /[^A-Za-z0-9]/.test(password),
            },
            {
                label: t("signup.rules.password.noSpace"),
                isValid: !/\s/.test(password) && password.length > 0,
            },
        ],
        [password, t],
    );

    const confirmRules = useMemo<ValidationRule[]>(
        () => [
            {
                label: t("signup.rules.confirm.match"),
                isValid: confirmPassword.length > 0 && !passwordMismatch,
            },
        ],
        [confirmPassword.length, passwordMismatch, t],
    );

    const onSubmit = async (event: FormEvent) => {
        event.preventDefault();
        setSubmitting(true);
        setErrorMessage("");
        setWarningMessage("");

        if (configLoading) {
            setWarningMessage(t("forgotPassword.configLoading"));
            setSubmitting(false);
            return;
        }
        if (!emailEnabled) {
            setWarningMessage(t("forgotPassword.disabled"));
            setSubmitting(false);
            return;
        }
        if (!token) {
            setErrorMessage(t("resetPassword.errors.missingToken"));
            setSubmitting(false);
            return;
        }
        if (!password.trim()) {
            setWarningMessage(t("auth.errors.requiredPassword"));
            setSubmitting(false);
            return;
        }
        if (!isValidPassword(password)) {
            setWarningMessage(t("auth.errors.invalidPasswordPattern"));
            setSubmitting(false);
            return;
        }
        if (!confirmPassword.trim()) {
            setWarningMessage(t("auth.errors.requiredConfirmPassword"));
            setSubmitting(false);
            return;
        }
        if (passwordMismatch) {
            setWarningMessage(t("auth.errors.passwordMismatch"));
            setSubmitting(false);
            return;
        }

        try {
            await resetPassword(token, password);
            navigate("/reset-password/success", { replace: true });
        } catch (nextError) {
            const detail = extractApiDetail(nextError);
            if (detail?.error === "EMAIL_DISABLED") {
                setWarningMessage(t("forgotPassword.disabled"));
            } else {
                setErrorMessage(
                    resolveAuthErrorMessage(t, detail, "resetPassword.errors.fallback"),
                );
            }
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <main className="page auth-page">
            <PanelCard
                className="auth-panel"
                title={t("resetPassword.title")}
                subtitle={t("resetPassword.subtitle")}
            >
                <form onSubmit={onSubmit} className="form" noValidate>
                    <InputField
                        label={t("resetPassword.passwordLabel")}
                        type="password"
                        autoComplete="new-password"
                        value={password}
                        onValueChange={setPassword}
                    />
                    <ValidationCard title={t("signup.validation.password")} rules={passwordRules} />
                    <InputField
                        label={t("resetPassword.confirmPasswordLabel")}
                        type="password"
                        autoComplete="new-password"
                        value={confirmPassword}
                        onValueChange={setConfirmPassword}
                    />
                    <ValidationCard title={t("signup.validation.confirm")} rules={confirmRules} />
                    {warningMessage ? (
                        <WarningCard title={t("cards.warningTitle")} message={warningMessage} />
                    ) : null}
                    {errorMessage ? (
                        <ErrorCard title={t("cards.errorTitle")} message={errorMessage} />
                    ) : null}
                    <Button
                        type="submit"
                        loading={submitting}
                        disabled={configLoading || !emailEnabled || passwordMismatch}
                    >
                        {t("resetPassword.submitIdle")}
                    </Button>
                </form>
                <p className="muted auth-footer">
                    {t("resetPassword.loginPrompt")}{" "}
                    <Link to="/login" className="text-link">
                        {t("resetPassword.loginLink")}
                    </Link>
                </p>
            </PanelCard>
        </main>
    );
}
