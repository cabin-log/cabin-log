import { useTranslation } from "react-i18next";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { useAuthContext } from "./hooks/useAuth";
import { useAppConfig } from "./hooks/useFeatures";
import { hasStartedFromLanding } from "./utils/landing";
import { LoginPage } from "./pages/login/LoginPage";
import { CabinInitPage } from "./pages/cabin/CabinInitPage";
import { LoadingPage } from "./pages/main/LoadingPage";
import { LandingPage } from "./pages/main/LandingPage";
import { NotFoundPage } from "./pages/main/NotFoundPage";
import { ServerUnavailablePage } from "./pages/main/ServerUnavailablePage";
import { useServerConnectivity } from "./hooks/connectivity/useServerConnectivity";

function ProtectedStandaloneRoute({
    children,
    loginEnabled,
    configLoading,
}: {
    children: ReactNode;
    loginEnabled: boolean;
    configLoading: boolean;
}) {
    const { user, loading } = useAuthContext();
    const { t } = useTranslation();

    if (loading || configLoading) {
        return <LoadingPage message={t("app.loadingSession")} />;
    }
    if (loginEnabled && !user) {
        return <Navigate to="/login" replace />;
    }

    return children;
}

function NotFoundRoute({ configLoading }: { configLoading: boolean }) {
    const { loading } = useAuthContext();

    if (loading || configLoading) {
        return <LoadingPage />;
    }

    return (
        <main className="page">
            <NotFoundPage />
        </main>
    );
}

export function App() {
    const { t } = useTranslation();
    const {
        data: appConfig,
        loading: configLoading,
        error: configError,
        reload: reloadConfig,
    } = useAppConfig();
    const { checkNow, status: connectivityStatus } = useServerConnectivity();
    const [retryingConfig, setRetryingConfig] = useState(false);
    const landingStarted = hasStartedFromLanding();

    useEffect(() => {
        delete document.documentElement.dataset.theme;
    }, []);

    if (configLoading) {
        return <LoadingPage message={t("app.loadingSession")} />;
    }
    if (!appConfig) {
        return (
            <ServerUnavailablePage
                checking={
                    retryingConfig ||
                    connectivityStatus === "checking" ||
                    connectivityStatus === "reconnecting"
                }
                error={configError}
                onRetry={() => {
                    setRetryingConfig(true);
                    void checkNow()
                        .then(() => reloadConfig())
                        .catch(() => undefined)
                        .finally(() => setRetryingConfig(false));
                }}
            />
        );
    }

    const loginEnabled = appConfig.login_enabled;

    return (
        <Routes>
            <Route
                path="/"
                element={
                    landingStarted ? (
                        <Navigate to={loginEnabled ? "/login" : "/cabin"} replace />
                    ) : (
                        <LandingPage loginEnabled={loginEnabled} />
                    )
                }
            />
            <Route
                path="/login"
                element={loginEnabled ? <LoginPage /> : <Navigate to="/cabin" replace />}
            />
            <Route path="/loading" element={<LoadingPage />} />
            <Route
                path="/login/success"
                element={<Navigate to="/cabin" replace state={{ playCabinEntryReveal: true }} />}
            />
            <Route
                path="/cabin"
                element={
                    <ProtectedStandaloneRoute
                        loginEnabled={loginEnabled}
                        configLoading={configLoading}
                    >
                        <CabinInitPage />
                    </ProtectedStandaloneRoute>
                }
            />
            <Route path="*" element={<NotFoundRoute configLoading={configLoading} />} />
        </Routes>
    );
}
