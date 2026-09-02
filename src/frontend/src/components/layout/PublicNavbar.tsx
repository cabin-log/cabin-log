import { useTranslation } from "react-i18next";

import { startDesktopWindowDrag } from "../../utils/desktopWindow";
import { BrandMark } from "../ui";
import { ConnectivityStatus } from "./ConnectivityStatus";

type PublicNavbarProps = {
    ariaLabel: string;
};

export function PublicNavbar({ ariaLabel }: PublicNavbarProps) {
    const { t } = useTranslation();

    return (
        <header
            className="public-nav"
            aria-label={ariaLabel}
            data-tauri-drag-region
            onMouseDown={startDesktopWindowDrag}
        >
            <div className="public-nav__inner" data-tauri-drag-region>
                <div className="public-nav__brand" data-tauri-drag-region>
                    <BrandMark className="brand-mark--nav" />
                </div>
                <p className="public-nav__title">{t("landing.eyebrow")}</p>
                <div className="public-nav__actions">
                    <ConnectivityStatus placement="navbar" />
                </div>
            </div>
        </header>
    );
}
