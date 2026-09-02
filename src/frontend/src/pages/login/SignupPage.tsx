import { FormEvent, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { InlineMessage } from "../../components/ui/status/InlineMessage";
import { ErrorCard, WarningCard } from "../../components/ui/status/StatusCard";
import {
    Button,
    InputField,
    PanelCard,
    ValidationCard,
    type ValidationRule,
} from "../../components/ui";
import { useAuthContext } from "../../hooks/useAuth";
import { useAuthApi } from "../../hooks/api/auth/useAuthApi";
import { useAppConfig } from "../../hooks/useFeatures";
import { isValidEmail, isValidPassword } from "../../utils/validation";

export function SignupPage() {
    const { t } = useTranslation();
    const { signup } = useAuthContext();
    const { extractApiDetail, resolveAuthErrorMessage } = useAuthApi();
    const { data: appConfig, loading: configLoading } = useAppConfig();
    const navigate = useNavigate();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [nameErrorMessage, setNameErrorMessage] = useState("");
    const [emailErrorMessage, setEmailErrorMessage] = useState("");
    const [passwordErrorMessage, setPasswordErrorMessage] = useState("");
    const [confirmPasswordErrorMessage, setConfirmPasswordErrorMessage] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const [warningMessage, setWarningMessage] = useState("");

    const passwordMismatch = confirmPassword.length > 0 && confirmPassword !== password;
    const hasFeedback = useMemo(
        () => Boolean(errorMessage || warningMessage),
        [errorMessage, warningMessage],
    );
    const emailRules = useMemo<ValidationRule[]>(
        () => [
            {
                label: t("signup.rules.email.format"),
                isValid: isValidEmail(email),
            },
        ],
        [email, t],
    );
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
    const emailEnabled = appConfig?.email_enabled === true;

    const onSubmit = async (event: FormEvent) => {
        event.preventDefault();
        setSubmitting(true);
        setNameErrorMessage("");
        setEmailErrorMessage("");
        setPasswordErrorMessage("");
        setConfirmPasswordErrorMessage("");
        setErrorMessage("");
        setWarningMessage("");

        if (configLoading) {
            setWarningMessage(t("signup.configLoading"));
            setSubmitting(false);
            return;
        }

        let hasEmptyField = false;
        if (!name.trim()) {
            setNameErrorMessage(t("auth.errors.requiredName"));
            hasEmptyField = true;
        }
        if (!email.trim()) {
            setEmailErrorMessage(t("auth.errors.requiredEmail"));
            hasEmptyField = true;
        }
        if (!password.trim()) {
            setPasswordErrorMessage(t("auth.errors.requiredPassword"));
            hasEmptyField = true;
        }
        if (!confirmPassword.trim()) {
            setConfirmPasswordErrorMessage(t("auth.errors.requiredConfirmPassword"));
            hasEmptyField = true;
        }

        if (hasEmptyField) {
            setSubmitting(false);
            return;
        }

        if (!isValidEmail(email)) {
            setWarningMessage(t("auth.errors.invalidEmail"));
            setSubmitting(false);
            return;
        }
        if (!isValidPassword(password)) {
            setWarningMessage(t("auth.errors.invalidPasswordPattern"));
            setSubmitting(false);
            return;
        }
        if (passwordMismatch) {
            setWarningMessage(t("auth.errors.passwordMismatch"));
            setSubmitting(false);
            return;
        }

        const normalizedEmail = email.trim();
        if (emailEnabled) {
            navigate("/signup/email-sent", {
                replace: true,
                state: { email: normalizedEmail },
            });
        } else {
            navigate("/signup/email-sent", { replace: true });
        }

        void signup({ name, email: normalizedEmail, password }).catch((nextError) => {
            const detail = extractApiDetail(nextError);
            const resolvedMessage = resolveAuthErrorMessage(
                t,
                detail,
                "auth.errors.signupFallback",
            );
            console.debug(
                "[auth] signup request failed after optimistic transition:",
                resolvedMessage,
            );
        });
        setSubmitting(false);
    };

    return (
        <main className="page auth-page">
            <PanelCard
                className="auth-panel"
                title={t("signup.title")}
                subtitle={t("signup.subtitle")}
            >
                <form onSubmit={onSubmit} className="form" noValidate>
                    <InputField
                        label={t("signup.fields.name")}
                        type="text"
                        autoComplete="name"
                        minLength={2}
                        maxLength={50}
                        value={name}
                        onValueChange={(value) => {
                            setName(value);
                            if (nameErrorMessage) {
                                setNameErrorMessage("");
                            }
                            if (warningMessage || errorMessage) {
                                setWarningMessage("");
                                setErrorMessage("");
                            }
                        }}
                    />
                    {nameErrorMessage ? <InlineMessage>{nameErrorMessage}</InlineMessage> : null}
                    <InputField
                        label={t("signup.fields.email")}
                        type="email"
                        autoComplete="email"
                        value={email}
                        onValueChange={(value) => {
                            setEmail(value);
                            if (emailErrorMessage) {
                                setEmailErrorMessage("");
                            }
                            if (warningMessage || errorMessage) {
                                setWarningMessage("");
                                setErrorMessage("");
                            }
                        }}
                    />
                    {emailErrorMessage ? <InlineMessage>{emailErrorMessage}</InlineMessage> : null}
                    <ValidationCard title={t("signup.validation.email")} rules={emailRules} />
                    <InputField
                        label={t("signup.fields.password")}
                        type="password"
                        autoComplete="new-password"
                        value={password}
                        onValueChange={(value) => {
                            setPassword(value);
                            if (passwordErrorMessage) {
                                setPasswordErrorMessage("");
                            }
                            if (warningMessage || errorMessage) {
                                setWarningMessage("");
                                setErrorMessage("");
                            }
                        }}
                    />
                    {passwordErrorMessage ? (
                        <InlineMessage>{passwordErrorMessage}</InlineMessage>
                    ) : null}
                    <ValidationCard title={t("signup.validation.password")} rules={passwordRules} />
                    <InputField
                        label={t("signup.fields.confirmPassword")}
                        type="password"
                        autoComplete="new-password"
                        value={confirmPassword}
                        onValueChange={(value) => {
                            setConfirmPassword(value);
                            if (confirmPasswordErrorMessage) {
                                setConfirmPasswordErrorMessage("");
                            }
                            if (warningMessage || errorMessage) {
                                setWarningMessage("");
                                setErrorMessage("");
                            }
                        }}
                    />
                    {confirmPasswordErrorMessage ? (
                        <InlineMessage>{confirmPasswordErrorMessage}</InlineMessage>
                    ) : null}
                    <ValidationCard title={t("signup.validation.confirm")} rules={confirmRules} />
                    {hasFeedback && warningMessage ? (
                        <WarningCard title={t("cards.warningTitle")} message={warningMessage} />
                    ) : null}
                    {hasFeedback && errorMessage ? (
                        <ErrorCard title={t("cards.errorTitle")} message={errorMessage} />
                    ) : null}
                    <Button
                        type="submit"
                        disabled={submitting || passwordMismatch || configLoading}
                    >
                        {t("signup.submitIdle")}
                    </Button>
                </form>
                <p className="muted auth-footer">
                    {t("signup.loginPrompt")}{" "}
                    <Link to="/login" className="text-link">
                        {t("signup.loginLink")}
                    </Link>
                </p>
            </PanelCard>
        </main>
    );
}
