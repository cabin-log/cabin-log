import { AppWindow, PanelLeftClose, PanelLeftOpen, Settings } from "lucide-react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { Tooltip } from "../ui";

type SidebarKey = "cabin" | "settings";

type AppSidebarProps = {
    expanded: boolean;
    onToggleExpanded: () => void;
};

export function AppSidebar({ expanded, onToggleExpanded }: AppSidebarProps) {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();

    const items = useMemo(
        () => [
            {
                key: "cabin" as const,
                label: t("nav.sidebar.cabin"),
                icon: AppWindow,
            },
            {
                key: "settings" as const,
                label: t("nav.sidebar.settings"),
                icon: Settings,
            },
        ],
        [t],
    );

    const activeKey: SidebarKey = location.pathname.startsWith("/settings") ? "settings" : "cabin";

    const handleSelect = (key: SidebarKey) => {
        if (key === "settings") {
            navigate("/settings");
            return;
        }
        navigate("/cabin");
    };

    const toggleLabel = expanded ? t("nav.sidebar.toggleClose") : t("nav.sidebar.toggleOpen");

    return (
        <aside className={expanded ? "app-sidebar app-sidebar--expanded" : "app-sidebar"}>
            <Tooltip content={toggleLabel} side="right" className="app-sidebar__toggle-tooltip">
                <button
                    type="button"
                    className="app-sidebar__toggle"
                    onClick={onToggleExpanded}
                    aria-label={toggleLabel}
                >
                    {expanded ? <PanelLeftClose /> : <PanelLeftOpen />}
                </button>
            </Tooltip>
            <nav className="app-sidebar__nav" aria-label={t("nav.sidebar.aria")}>
                {items.map(({ key, label, icon: Icon }) => {
                    const isActive = activeKey === key;
                    const buttonClassName = isActive
                        ? "app-sidebar__item app-sidebar__item--active"
                        : "app-sidebar__item";
                    return (
                        <Tooltip
                            key={key}
                            content={label}
                            side="right"
                            disabled={expanded}
                            className="app-sidebar__item-tooltip"
                        >
                            <button
                                type="button"
                                className={buttonClassName}
                                onClick={() => handleSelect(key)}
                                aria-current={isActive ? "page" : undefined}
                                aria-label={label}
                            >
                                <span className="app-sidebar__item-icon" aria-hidden="true">
                                    <Icon />
                                </span>
                                {expanded ? (
                                    <span className="app-sidebar__item-label">{label}</span>
                                ) : null}
                            </button>
                        </Tooltip>
                    );
                })}
            </nav>
        </aside>
    );
}
