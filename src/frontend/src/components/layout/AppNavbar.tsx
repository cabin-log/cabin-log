import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuthContext } from "../../hooks/useAuth";
import { useServerConnectivity } from "../../hooks/connectivity/useServerConnectivity";
import { useAppConfig } from "../../hooks/useFeatures";
import { startDesktopWindowDrag } from "../../utils/desktopWindow";
import { BrandMark, Tooltip } from "../ui";
import { ConnectivityStatus } from "./ConnectivityStatus";
import { ProfileDropdown } from "./ProfileDropdown";

export function AppNavbar() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();
    const { user, logout } = useAuthContext();
    const { data: appConfig } = useAppConfig();
    const { checkNow, isDesktop, status: connectivityStatus } = useServerConnectivity();
    const [busy, setBusy] = useState(false);
    const loginEnabled = appConfig?.login_enabled === true;
    const logoutBlockedByConnectivity = isDesktop && connectivityStatus !== "online";

    const displayName = user?.name?.trim() || user?.email;
    const avatarLabel = displayName?.slice(0, 1).toUpperCase();
    let pageTitle = t("nav.pageTitles.cabin");
    if (location.pathname === "/settings") {
        pageTitle = t("nav.pageTitles.settings");
    } else if (location.pathname === "/loading") {
        pageTitle = t("nav.pageTitles.loading");
    } else if (location.pathname !== "/cabin") {
        pageTitle = t("nav.pageTitles.notFound");
    }

    const onLogout = async () => {
        if (logoutBlockedByConnectivity) {
            void checkNow();
            return;
        }

        setBusy(true);
        try {
            await logout();
            navigate(loginEnabled ? "/login" : "/cabin", { replace: true });
        } finally {
            setBusy(false);
        }
    };

    return (
        <header className="app-nav" data-tauri-drag-region onMouseDown={startDesktopWindowDrag}>
            <div className="app-nav__inner" data-tauri-drag-region>
                <Tooltip content={t("nav.aria.goCabin")} side="right">
                    <Link to="/cabin" className="app-nav__brand" aria-label={t("nav.aria.goCabin")}>
                        <BrandMark className="brand-mark--nav" />
                    </Link>
                </Tooltip>
                <p className="app-nav__title">{pageTitle}</p>
                <div className="app-nav__actions">
                    <ConnectivityStatus placement="navbar" />
                    {user && displayName && avatarLabel ? (
                        <ProfileDropdown
                            avatarLabel={avatarLabel}
                            avatarImageUrl={user.profile_image_url}
                            busy={busy}
                            displayName={displayName}
                            email={user.email}
                            onLogout={() => void onLogout()}
                            logoutDisabled={logoutBlockedByConnectivity}
                            logoutDisabledTitle={t("nav.logoutUnavailable")}
                            showLogout={loginEnabled}
                        />
                    ) : null}
                </div>
            </div>
        </header>
    );
}
