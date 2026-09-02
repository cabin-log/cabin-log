import { LogOut, Settings } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import { UserAvatar } from "../ui";

type ProfileDropdownProps = {
    avatarLabel: string;
    avatarImageUrl?: string | null;
    busy: boolean;
    displayName: string;
    email?: string;
    onLogout: () => void;
    logoutDisabled?: boolean;
    logoutDisabledTitle?: string;
    showLogout: boolean;
};

export function ProfileDropdown({
    avatarLabel,
    avatarImageUrl,
    busy,
    displayName,
    email,
    onLogout,
    logoutDisabled = false,
    logoutDisabledTitle,
    showLogout,
}: ProfileDropdownProps) {
    const { t } = useTranslation();
    const location = useLocation();
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        setMenuOpen(false);
    }, [location.pathname]);

    useEffect(() => {
        if (!menuOpen) return;

        const onPointerDown = (event: MouseEvent) => {
            if (!menuRef.current?.contains(event.target as Node)) {
                setMenuOpen(false);
            }
        };

        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                setMenuOpen(false);
            }
        };

        document.addEventListener("mousedown", onPointerDown);
        document.addEventListener("keydown", onKeyDown);

        return () => {
            document.removeEventListener("mousedown", onPointerDown);
            document.removeEventListener("keydown", onKeyDown);
        };
    }, [menuOpen]);

    return (
        <div className="profile-menu" ref={menuRef}>
            <button
                type="button"
                className="profile-menu__trigger"
                aria-label={t("nav.aria.openMenu")}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen((prev) => !prev)}
                title={displayName}
            >
                <UserAvatar
                    className="profile-menu__avatar"
                    imageUrl={avatarImageUrl}
                    label={avatarLabel}
                />
            </button>
            {menuOpen ? (
                <div
                    className="profile-menu__dropdown"
                    role="menu"
                    aria-label={t("nav.profileMenu")}
                >
                    <div className="profile-menu__identity">
                        <p className="profile-menu__name">{displayName}</p>
                        <p className="profile-menu__email">{email}</p>
                    </div>
                    <Link to="/settings" className="profile-menu__item" role="menuitem">
                        <span className="profile-menu__item-icon" aria-hidden="true">
                            <Settings />
                        </span>
                        <span>{t("nav.settings")}</span>
                    </Link>
                    {showLogout ? (
                        <button
                            type="button"
                            className="profile-menu__item profile-menu__item--danger"
                            role="menuitem"
                            onClick={onLogout}
                            disabled={busy || logoutDisabled}
                            title={logoutDisabled ? logoutDisabledTitle : undefined}
                        >
                            <span className="profile-menu__item-icon" aria-hidden="true">
                                <LogOut />
                            </span>
                            <span>{busy ? t("nav.logoutBusy") : t("nav.logoutIdle")}</span>
                        </button>
                    ) : null}
                </div>
            ) : null}
        </div>
    );
}
