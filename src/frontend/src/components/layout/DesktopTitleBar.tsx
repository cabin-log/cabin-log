import { Minus, Square, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import { getCurrentWindow } from "@tauri-apps/api/window";

import { detectDesktopPlatform, isTauriRuntime } from "../../utils/desktopRuntime";
import { startDesktopWindowDrag } from "../../utils/desktopWindow";
import { ConnectivityStatus } from "./ConnectivityStatus";

const STANDALONE_TITLEBAR_PATHS = [
    "/forgot-password",
    "/loading",
    "/login",
    "/reset-password",
    "/signup",
    "/verify-email",
];

export function DesktopTitleBar() {
    const { t } = useTranslation();
    const location = useLocation();
    const tauriRuntime = typeof window !== "undefined" && isTauriRuntime(window);
    if (!tauriRuntime) return null;

    const platform = detectDesktopPlatform(window.navigator.userAgent);
    const standalone = STANDALONE_TITLEBAR_PATHS.some(
        (path) => location.pathname === path || location.pathname.startsWith(`${path}/`),
    );
    const className = standalone
        ? "desktop-titlebar desktop-titlebar--standalone"
        : "desktop-titlebar desktop-titlebar--integrated";
    const appWindow = getCurrentWindow();
    const runWindowAction = (action: () => Promise<void>) => {
        void action().catch((error: unknown) => {
            console.error("Desktop window action failed.", error);
        });
    };

    return (
        <div
            className={className}
            data-tauri-drag-region={standalone ? "" : undefined}
            onMouseDown={standalone ? startDesktopWindowDrag : undefined}
            onDoubleClick={
                standalone && platform !== "macos"
                    ? () => runWindowAction(() => appWindow.toggleMaximize())
                    : undefined
            }
        >
            {standalone ? (
                <div className="desktop-titlebar__tools">
                    <ConnectivityStatus placement="titlebar" />
                </div>
            ) : null}
            {platform !== "macos" ? (
                <div className="desktop-titlebar__controls">
                    <button
                        type="button"
                        className="desktop-titlebar__button"
                        aria-label={t("desktopWindow.minimize")}
                        onClick={() => runWindowAction(() => appWindow.minimize())}
                    >
                        <Minus aria-hidden="true" />
                    </button>
                    <button
                        type="button"
                        className="desktop-titlebar__button"
                        aria-label={t("desktopWindow.maximize")}
                        onClick={() => runWindowAction(() => appWindow.toggleMaximize())}
                    >
                        <Square aria-hidden="true" />
                    </button>
                    <button
                        type="button"
                        className="desktop-titlebar__button desktop-titlebar__button--close"
                        aria-label={t("desktopWindow.close")}
                        onClick={() => runWindowAction(() => appWindow.close())}
                    >
                        <X aria-hidden="true" />
                    </button>
                </div>
            ) : null}
        </div>
    );
}
