import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";

import { AppNavbar } from "./components/layout/AppNavbar";
import { AppSidebar } from "./components/layout/AppSidebar";
import { useAuthContext } from "./hooks/useAuth";
import { useAppConfig } from "./hooks/useFeatures";
import { hasStartedFromLanding } from "./utils/landing";
import { LoginPage } from "./pages/login/LoginPage";
import { LoginSuccessPage } from "./pages/login/LoginSuccessPage";
import { LoadingPage } from "./pages/main/LoadingPage";
import { LandingPage } from "./pages/main/LandingPage";
import { ShowCaseNotFoundPage } from "./pages/main/ShowCaseNotFoundPage";
import { ShowCasePage } from "./pages/main/ShowCasePage";
import { SettingsPage } from "./pages/settings/SettingsPage";
import { ServerUnavailablePage } from "./pages/main/ServerUnavailablePage";
import { useServerConnectivity } from "./hooks/connectivity/useServerConnectivity";

function ProtectedLayout({
    loginEnabled,
    configLoading,
}: {
    loginEnabled: boolean;
    configLoading: boolean;
}) {
    const { user, loading } = useAuthContext();
    const { t } = useTranslation();
    const location = useLocation();
    const isMainPage = location.pathname === "/show-case";
    const [sidebarExpanded, setSidebarExpanded] = useState(false);

    useEffect(() => {
        if (!isMainPage) {
            setSidebarExpanded(false);
        }
    }, [isMainPage]);

    if (loading || configLoading) {
        return <LoadingPage message={t("app.loadingSession")} />;
    }
    if (loginEnabled && !user) {
        return <Navigate to="/login" replace />;
    }

    const mainClassName = isMainPage
        ? sidebarExpanded
            ? "app-main app-main--with-sidebar app-main--sidebar-expanded"
            : "app-main app-main--with-sidebar app-main--sidebar-collapsed"
        : "app-main";

    return (
        <div className="app-shell">
            <AppNavbar />
            <div className="app-body">
                {isMainPage ? (
                    <AppSidebar
                        expanded={sidebarExpanded}
                        onToggleExpanded={() => {
                            setSidebarExpanded((prev) => !prev);
                        }}
                    />
                ) : null}
                <main className={mainClassName}>
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

function NotFoundRoute({
    loginEnabled,
    configLoading,
}: {
    loginEnabled: boolean;
    configLoading: boolean;
}) {
    const { user, loading } = useAuthContext();

    if (loading || configLoading) {
        return <LoadingPage />;
    }

    if (user || !loginEnabled) {
        return (
            <div className="app-shell">
                <AppNavbar />
                <main className="app-main">
                    <ShowCaseNotFoundPage />
                </main>
            </div>
        );
    }

    return (
        <main className="page">
            <ShowCaseNotFoundPage />
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
                        <Navigate to={loginEnabled ? "/login" : "/show-case"} replace />
                    ) : (
                        <LandingPage loginEnabled={loginEnabled} />
                    )
                }
            />
            <Route
                path="/login"
                element={loginEnabled ? <LoginPage /> : <Navigate to="/show-case" replace />}
            />
            <Route path="/loading" element={<LoadingPage />} />
            <Route path="/signup/*" element={<Navigate to="/login" replace />} />
            <Route path="/forgot-password/*" element={<Navigate to="/login" replace />} />
            <Route path="/reset-password/*" element={<Navigate to="/login" replace />} />
            <Route path="/verify-email" element={<Navigate to="/login" replace />} />
            <Route
                element={
                    <ProtectedLayout loginEnabled={loginEnabled} configLoading={configLoading} />
                }
            >
                <Route path="/dashboard" element={<Navigate to="/show-case" replace />} />
                <Route path="/login/success" element={<LoginSuccessPage />} />
                <Route path="/show-case" element={<ShowCasePage />} />
                <Route
                    path="/show-case/loading"
                    element={<LoadingPage message="Loading preview..." />}
                />
                <Route path="/show-case/404" element={<ShowCaseNotFoundPage />} />
                <Route path="/settings" element={<SettingsPage />} />
            </Route>
            <Route
                path="*"
                element={
                    <NotFoundRoute loginEnabled={loginEnabled} configLoading={configLoading} />
                }
            />
        </Routes>
    );
}
