import { Activity, Box, Coins, LogOut, Package, RefreshCw, Settings, Utensils } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

import {
    Button,
    InlineMessage,
    Modal,
    PanelCard,
    Spinner,
    Tooltip,
    UserAvatar,
} from "../../components/ui";
import { CabinPhaserStage } from "../../components/features/cabin/CabinPhaserStage";
import { useGameApi, type GameState } from "../../hooks/api/game/useGameApi";
import { useAuthContext } from "../../hooks/useAuth";
import { consumeCabinEntryReveal } from "../../utils/cabinEntryReveal";

type CabinModal = "packages" | "settings" | null;
const SUPPORTED_LANGUAGE_IDS = ["en", "ko"] as const;
type SupportedLanguageId = (typeof SUPPORTED_LANGUAGE_IDS)[number];
type CabinRouteState = {
    playCabinEntryReveal?: boolean;
};

function formatNumber(value: number): string {
    return new Intl.NumberFormat().format(value);
}

function useCabinState() {
    const { t } = useTranslation();
    const { getGameState, extractGameErrorDetail, resolveGameErrorMessage } = useGameApi();
    const [state, setState] = useState<GameState | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const payload = await getGameState();
            setState(payload);
            setError(null);
        } catch (caught) {
            setError(
                resolveGameErrorMessage(
                    t,
                    extractGameErrorDetail(caught),
                    "cabin.errors.stateLoadFailed",
                ),
            );
        } finally {
            setLoading(false);
        }
    }, [extractGameErrorDetail, getGameState, resolveGameErrorMessage, t]);

    useEffect(() => {
        void load();
    }, [load]);

    return { error, load, loading, state };
}

export function CabinInitPage() {
    const { i18n, t } = useTranslation();
    const location = useLocation();
    const navigate = useNavigate();
    const { logout, user } = useAuthContext();
    const { error, load, loading, state } = useCabinState();
    const [activeModal, setActiveModal] = useState<CabinModal>(null);
    const [logoutBusy, setLogoutBusy] = useState(false);
    const displayName = user?.name?.trim() || user?.email || t("cabin.player.fallbackName");
    const isGithubConnected = user?.oauth_providers?.includes("github") === true;
    const routeState = location.state as CabinRouteState | null;
    const [shouldPlayEntryReveal] = useState(
        () => routeState?.playCabinEntryReveal === true || consumeCabinEntryReveal(),
    );
    const pendingPackages = state?.pending_packages ?? [];
    const stackProfiles = state?.stack_profiles.items ?? [];
    const topStacks = useMemo(() => stackProfiles.slice(0, 5), [stackProfiles]);
    const normalizedLanguageId =
        (i18n.resolvedLanguage ?? i18n.language ?? "en").split("-")[0] || "en";
    const currentLanguageId: SupportedLanguageId = SUPPORTED_LANGUAGE_IDS.includes(
        normalizedLanguageId as SupportedLanguageId,
    )
        ? (normalizedLanguageId as SupportedLanguageId)
        : "en";
    const onLogout = async () => {
        setLogoutBusy(true);
        try {
            await logout();
            navigate("/login", { replace: true });
        } finally {
            setLogoutBusy(false);
        }
    };

    return (
        <main
            className={
                shouldPlayEntryReveal
                    ? "page auth-page cabin-init-page cabin-init-page--entry-reveal"
                    : "page auth-page cabin-init-page"
            }
        >
            <div className="cabin-init-hud" aria-label={t("cabin.hud.aria")}>
                <div className="cabin-init-player">
                    <UserAvatar
                        className="cabin-init-player__avatar"
                        imageUrl={user?.profile_image_url}
                        label={displayName}
                    />
                    <div>
                        <p className="cabin-init-player__name">{displayName}</p>
                        <p className="cabin-init-player__meta">{t("cabin.player.ready")}</p>
                    </div>
                </div>
                <div className="cabin-init-actions">
                    <Tooltip content={t("cabin.actions.packages")} side="bottom">
                        <button
                            type="button"
                            className="cabin-init-icon-button"
                            onClick={() => setActiveModal("packages")}
                            aria-label={t("cabin.actions.packages")}
                        >
                            <Package aria-hidden="true" />
                            {pendingPackages.length > 0 ? (
                                <span className="cabin-init-icon-button__badge">
                                    {pendingPackages.length}
                                </span>
                            ) : null}
                        </button>
                    </Tooltip>
                    <Tooltip content={t("cabin.actions.settings")} side="bottom">
                        <button
                            type="button"
                            className="cabin-init-icon-button"
                            onClick={() => setActiveModal("settings")}
                            aria-label={t("cabin.actions.settings")}
                        >
                            <Settings aria-hidden="true" />
                        </button>
                    </Tooltip>
                </div>
            </div>

            <section className="cabin-init-stage" aria-label={t("cabin.stage.aria")}>
                <CabinPhaserStage
                    ariaLabel={t("cabin.stage.phaserAria")}
                    cabin={state?.cabin ?? null}
                    zoomControlsLabel={t("cabin.actions.zoomControls")}
                    zoomInLabel={t("cabin.actions.zoomIn")}
                    zoomOutLabel={t("cabin.actions.zoomOut")}
                />
                <PanelCard className="cabin-init-panel">
                    {loading ? (
                        <div className="cabin-init-panel__loading">
                            <Spinner size="lg" label={t("cabin.state.loading")} />
                        </div>
                    ) : null}
                    {error ? (
                        <div className="cabin-init-panel__error">
                            <InlineMessage>{error}</InlineMessage>
                            <Button type="button" onClick={() => void load()}>
                                <RefreshCw aria-hidden="true" />
                                {t("cabin.actions.retry")}
                            </Button>
                        </div>
                    ) : null}
                    {!loading && !error && state ? (
                        <div className="cabin-init-board">
                            <div className="cabin-init-board__stat">
                                <Coins aria-hidden="true" />
                                <span>{t("cabin.stats.coins")}</span>
                                <strong>{formatNumber(state.wallet.coins)}</strong>
                            </div>
                            <div className="cabin-init-board__stat">
                                <Activity aria-hidden="true" />
                                <span>{t("cabin.stats.today")}</span>
                                <strong>{formatNumber(state.today.total_activity_count)}</strong>
                            </div>
                            <div className="cabin-init-board__stat">
                                <Utensils aria-hidden="true" />
                                <span>{t("cabin.stats.food")}</span>
                                <strong>{formatNumber(state.today.food)}</strong>
                            </div>
                            <div className="cabin-init-board__stat">
                                <Box aria-hidden="true" />
                                <span>{t("cabin.stats.packages")}</span>
                                <strong>{formatNumber(pendingPackages.length)}</strong>
                            </div>
                        </div>
                    ) : null}
                </PanelCard>
            </section>

            <Modal
                className="cabin-init-modal"
                open={activeModal === "packages"}
                title={t("cabin.packages.title")}
                description={t("cabin.packages.description")}
                closeLabel={t("cabin.modal.close")}
                onClose={() => setActiveModal(null)}
            >
                {pendingPackages.length > 0 ? (
                    <div className="cabin-init-package-list">
                        {pendingPackages.map((item) => (
                            <article className="cabin-init-package" key={item.id}>
                                <div>
                                    <h3>{item.title}</h3>
                                    <p>{item.description || t("cabin.packages.noDescription")}</p>
                                </div>
                                <span>{item.items?.length ?? 0}</span>
                            </article>
                        ))}
                    </div>
                ) : (
                    <p className="cabin-init-empty">{t("cabin.packages.empty")}</p>
                )}
            </Modal>

            <Modal
                className="cabin-init-modal"
                open={activeModal === "settings"}
                title={t("cabin.settings.title")}
                description={t("cabin.settings.description")}
                closeLabel={t("cabin.modal.close")}
                onClose={() => setActiveModal(null)}
            >
                <div className="cabin-init-settings-content">
                    <section
                        className="cabin-init-settings-card cabin-init-settings-card--profile"
                        aria-label={t("cabin.settings.profileTitle")}
                    >
                        <UserAvatar
                            className="cabin-init-settings-profile__avatar"
                            imageUrl={user?.profile_image_url}
                            label={displayName}
                        />
                        <div className="cabin-init-settings-profile__copy">
                            <h3>{displayName}</h3>
                            <p>{user?.email}</p>
                            <span>
                                {isGithubConnected
                                    ? t("cabin.settings.githubConnected")
                                    : t("cabin.settings.githubUnknown")}
                            </span>
                        </div>
                    </section>

                    <section
                        className="cabin-init-settings-card"
                        aria-label={t("cabin.settings.language")}
                    >
                        <div className="cabin-init-settings-card__header">
                            <h3>{t("cabin.settings.language")}</h3>
                            <p>{t("cabin.settings.languageDescription")}</p>
                        </div>
                        <div className="cabin-init-language-control" role="group">
                            {SUPPORTED_LANGUAGE_IDS.map((languageId) => (
                                <button
                                    key={languageId}
                                    type="button"
                                    className={
                                        currentLanguageId === languageId
                                            ? "cabin-init-language-control__button cabin-init-language-control__button--active"
                                            : "cabin-init-language-control__button"
                                    }
                                    aria-pressed={currentLanguageId === languageId}
                                    onClick={() => {
                                        void i18n.changeLanguage(languageId);
                                    }}
                                >
                                    {t(`cabin.settings.languages.${languageId}`)}
                                </button>
                            ))}
                        </div>
                    </section>

                    <section
                        className="cabin-init-settings-card"
                        aria-label={t("cabin.settings.playTitle")}
                    >
                        <div className="cabin-init-settings-card__header">
                            <h3>{t("cabin.settings.playTitle")}</h3>
                            <p>{t("cabin.settings.playDescription")}</p>
                        </div>
                        <dl className="cabin-init-settings-list">
                            <div>
                                <dt>{t("cabin.settings.timezone")}</dt>
                                <dd>{state?.settings.timezone ?? t("cabin.settings.unknown")}</dd>
                            </div>
                            <div>
                                <dt>{t("cabin.settings.cutoff")}</dt>
                                <dd>
                                    {state
                                        ? t("cabin.settings.cutoffValue", {
                                              hour: state.settings.daily_cutoff_hour,
                                          })
                                        : t("cabin.settings.unknown")}
                                </dd>
                            </div>
                            <div>
                                <dt>{t("cabin.settings.cabin")}</dt>
                                <dd>
                                    {state
                                        ? t("cabin.settings.cabinValue", {
                                              width: state.cabin.width,
                                              depth: state.cabin.depth,
                                              tileWidth: state.cabin.tile_width,
                                              tileHeight: state.cabin.tile_height,
                                          })
                                        : t("cabin.settings.unknown")}
                                </dd>
                            </div>
                            <div>
                                <dt>{t("cabin.settings.stacks")}</dt>
                                <dd>
                                    {topStacks.length > 0
                                        ? topStacks.map((item) => item.language).join(", ")
                                        : t("cabin.settings.noStacks")}
                                </dd>
                            </div>
                        </dl>
                    </section>
                </div>
                <Button
                    type="button"
                    className="cabin-init-settings-logout"
                    loading={logoutBusy}
                    onClick={() => void onLogout()}
                >
                    <LogOut aria-hidden="true" />
                    {logoutBusy ? t("cabin.settings.logoutBusy") : t("cabin.settings.logoutIdle")}
                </Button>
            </Modal>
        </main>
    );
}
