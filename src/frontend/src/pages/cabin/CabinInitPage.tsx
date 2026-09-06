import {
    Activity,
    Armchair,
    Backpack,
    BookOpen,
    Box,
    Check,
    Coins,
    ImageOff,
    LogOut,
    Package,
    PawPrint,
    RefreshCw,
    Settings,
    Utensils,
} from "lucide-react";
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
import {
    useGameApi,
    type CabinPlacement,
    type GameState,
    type RewardPackage,
} from "../../hooks/api/game/useGameApi";
import { useAuthContext } from "../../hooks/useAuth";
import { markCabinDailySyncComplete, shouldRunCabinDailySync } from "../../utils/cabinDailySync";
import { consumeCabinEntryReveal } from "../../utils/cabinEntryReveal";

type CabinModal = "collection" | "inventory" | "packages" | "settings" | null;
const SUPPORTED_LANGUAGE_IDS = ["en", "ko"] as const;
type SupportedLanguageId = (typeof SUPPORTED_LANGUAGE_IDS)[number];
type InventoryTab = "supplies" | "furniture" | "petLogs";
type CollectionTab = "furniture" | "petLogs";
type CollectionEntry = NonNullable<NonNullable<GameState["collection"]>["furniture"]>[number];
type InventorySupplyItem = NonNullable<
    NonNullable<GameState["categorized_inventory"]>["supplies"]
>[number];
type InventoryRewardItem = NonNullable<
    NonNullable<GameState["categorized_inventory"]>["furniture"]
>[number];
type CabinRouteState = {
    playCabinEntryReveal?: boolean;
};

type InventoryDisplayItem =
    | {
          kind: "supply";
          key: string;
          title: string;
          assetKey: string;
          quantity: number;
      }
    | {
          kind: "reward";
          key: string;
          title: string;
          assetKey: string;
          sourceLanguage: string;
          level: number;
          stage: number;
          placement: CabinPlacement | null;
      };

function formatNumber(value: number): string {
    return new Intl.NumberFormat().format(value);
}

function getStringMetadataValue(
    metadata: Record<string, unknown> | undefined,
    key: string,
): string | null {
    const value = metadata?.[key];
    return typeof value === "string" && value.trim() ? value : null;
}

function resolvePackageDisplayText(
    item: RewardPackage,
    t: ReturnType<typeof useTranslation>["t"],
): { title: string; description: string } {
    const metadata = item.metadata as Record<string, unknown> | undefined;
    const grantType = getStringMetadataValue(metadata, "grant_type");
    if (grantType === "onboarding") {
        return {
            title: t("cabin.packages.onboardingTitle"),
            description: t("cabin.packages.onboardingDescription"),
        };
    }

    const rewardKey = getStringMetadataValue(metadata, "reward_key");
    if (grantType === "event_reward" && rewardKey) {
        const rewardName = resolveRewardName(rewardKey, "Achievement", t);
        return {
            title: t("cabin.packages.eventTitle", { reward: rewardName }),
            description: t("cabin.packages.eventDescription", { reward: rewardName }),
        };
    }

    const language = getStringMetadataValue(metadata, "language");
    if (language) {
        return {
            title: t("cabin.packages.stackOriginTitle", { language }),
            description: t("cabin.packages.stackOriginDescription", { language }),
        };
    }

    const rewardDate = getStringMetadataValue(metadata, "reward_date");
    if (item.source === "DAILY_REWARD" && rewardDate) {
        return {
            title: t("cabin.packages.dailyTitle", { date: rewardDate }),
            description: t("cabin.packages.dailyDescription"),
        };
    }

    return {
        title: item.title,
        description: item.description || t("cabin.packages.noDescription"),
    };
}

function resolveRewardName(
    rewardKey: string,
    language: string,
    t: ReturnType<typeof useTranslation>["t"],
): string {
    return t(`cabin.rewards.${rewardKey}`, { defaultValue: `${language} reward` });
}

function resolveSupplyName(itemKey: string, t: ReturnType<typeof useTranslation>["t"]): string {
    return t(`cabin.supplies.${itemKey}`, { defaultValue: itemKey });
}

function getCollectionRequirementText(
    item: CollectionEntry,
    t: ReturnType<typeof useTranslation>["t"],
): string {
    const conditionKey = item.condition_key ?? "stack_bytes";
    if (conditionKey !== "stack_bytes") {
        return t(`cabin.collection.conditions.${conditionKey}`, {
            defaultValue: t("cabin.collection.conditions.achievement"),
        });
    }
    return t("cabin.collection.requirement", {
        language: item.source_language,
        bytes: formatNumber(item.required_bytes ?? 50000),
        activities: formatNumber(item.required_recent_activity_count ?? 10),
    });
}

function getRewardAssetKey(rewardKey: string, collectionItems: CollectionEntry[]): string {
    const collectionItem = collectionItems.find((item) => item.reward_key === rewardKey);
    return collectionItem?.asset_key ?? rewardKey.split(".").at(-1) ?? rewardKey;
}

function getAssetPath(assetKey: string): string {
    return `/sprites/rewards/icons/${assetKey}.png`;
}

function AssetPreview({
    alt,
    assetKey,
    label,
    size = "sm",
}: {
    alt: string;
    assetKey: string;
    label: string;
    size?: "sm" | "lg";
}) {
    const [failedAssetKey, setFailedAssetKey] = useState<string | null>(null);
    const src = getAssetPath(assetKey);
    const hasFailed = failedAssetKey === assetKey;

    return (
        <div
            className={
                size === "lg"
                    ? "cabin-init-asset-preview cabin-init-asset-preview--lg"
                    : "cabin-init-asset-preview"
            }
        >
            {hasFailed ? (
                <span className="cabin-init-asset-preview__fallback">
                    <span>{label}</span>
                    <ImageOff aria-hidden="true" />
                </span>
            ) : (
                <img src={src} alt={alt} onError={() => setFailedAssetKey(assetKey)} />
            )}
        </div>
    );
}

function useCabinState(userId: number | null | undefined) {
    const { t } = useTranslation();
    const {
        claimRewardPackage,
        deleteCabinPlacement,
        getGameState,
        extractGameErrorDetail,
        resolveGameErrorMessage,
        syncRewardPackages,
    } = useGameApi();
    const [state, setState] = useState<GameState | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [claimingPackageId, setClaimingPackageId] = useState<number | null>(null);
    const [removingPlacementId, setRemovingPlacementId] = useState<number | null>(null);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            let payload = await getGameState();
            if (userId && shouldRunCabinDailySync(userId, payload.today.reward_date)) {
                await syncRewardPackages();
                markCabinDailySyncComplete(userId, payload.today.reward_date);
                payload = await getGameState();
            }
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
    }, [
        extractGameErrorDetail,
        getGameState,
        resolveGameErrorMessage,
        syncRewardPackages,
        t,
        userId,
    ]);

    const refresh = useCallback(async () => {
        setRefreshing(true);
        try {
            await syncRewardPackages();
            const payload = await getGameState();
            if (userId) {
                markCabinDailySyncComplete(userId, payload.today.reward_date);
            }
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
            setRefreshing(false);
        }
    }, [
        extractGameErrorDetail,
        getGameState,
        resolveGameErrorMessage,
        syncRewardPackages,
        t,
        userId,
    ]);

    const claimPackage = useCallback(
        async (packageId: number) => {
            setClaimingPackageId(packageId);
            try {
                await claimRewardPackage(packageId);
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
                setClaimingPackageId(null);
            }
        },
        [claimRewardPackage, extractGameErrorDetail, getGameState, resolveGameErrorMessage, t],
    );

    const removeCabinPlacement = useCallback(
        async (placementId: number) => {
            setRemovingPlacementId(placementId);
            try {
                await deleteCabinPlacement(placementId);
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
                setRemovingPlacementId(null);
            }
        },
        [deleteCabinPlacement, extractGameErrorDetail, getGameState, resolveGameErrorMessage, t],
    );

    useEffect(() => {
        void load();
    }, [load]);

    return {
        claimPackage,
        claimingPackageId,
        error,
        load,
        loading,
        refresh,
        refreshing,
        removeCabinPlacement,
        removingPlacementId,
        state,
    };
}

export function CabinInitPage() {
    const { i18n, t } = useTranslation();
    const location = useLocation();
    const navigate = useNavigate();
    const { logout, user } = useAuthContext();
    const {
        claimPackage,
        claimingPackageId,
        error,
        load,
        loading,
        refresh,
        refreshing,
        removeCabinPlacement,
        removingPlacementId,
        state,
    } = useCabinState(user?.id);
    const [activeModal, setActiveModal] = useState<CabinModal>(null);
    const [inventoryTab, setInventoryTab] = useState<InventoryTab>("supplies");
    const [collectionTab, setCollectionTab] = useState<CollectionTab>("furniture");
    const [selectedInventoryKey, setSelectedInventoryKey] = useState<string | null>(null);
    const [selectedCollectionKey, setSelectedCollectionKey] = useState<string | null>(null);
    const [logoutBusy, setLogoutBusy] = useState(false);
    const displayName = user?.name?.trim() || user?.email || t("cabin.player.fallbackName");
    const isGithubConnected = user?.oauth_providers?.includes("github") === true;
    const routeState = location.state as CabinRouteState | null;
    const [shouldPlayEntryReveal] = useState(
        () => routeState?.playCabinEntryReveal === true || consumeCabinEntryReveal(),
    );
    const pendingPackages = state?.pending_packages ?? [];
    const inventory = state?.categorized_inventory;
    const collection = state?.collection;
    const inventorySupplies = inventory?.supplies ?? [];
    const inventoryFurniture = inventory?.furniture ?? [];
    const inventoryPetLogs = inventory?.pet_logs ?? [];
    const collectionFurniture = collection?.furniture ?? [];
    const collectionPetLogs = collection?.pet_logs ?? [];
    const allCollectionItems = useMemo(
        () => [...collectionFurniture, ...collectionPetLogs],
        [collectionFurniture, collectionPetLogs],
    );
    const cabinPlacements = state?.cabin.placements ?? [];
    const buildRewardInventoryItem = useCallback(
        (item: InventoryRewardItem): InventoryDisplayItem => {
            const placement =
                cabinPlacements.find(
                    (placementItem) => placementItem.object_key === item.reward_key,
                ) ?? null;
            return {
                kind: "reward",
                key: item.reward_key,
                title: resolveRewardName(item.reward_key, item.source_language, t),
                assetKey: getRewardAssetKey(item.reward_key, allCollectionItems),
                sourceLanguage: item.source_language,
                level: item.stack_reward_level,
                stage: item.stage,
                placement,
            };
        },
        [allCollectionItems, cabinPlacements, t],
    );
    const visibleInventoryItems: InventoryDisplayItem[] = useMemo(() => {
        if (inventoryTab === "supplies") {
            return inventorySupplies.map((item: InventorySupplyItem) => ({
                kind: "supply",
                key: item.item_key,
                title: resolveSupplyName(item.item_key, t),
                assetKey: item.item_key,
                quantity: item.quantity,
            }));
        }
        if (inventoryTab === "furniture") {
            return inventoryFurniture.map(buildRewardInventoryItem);
        }
        return inventoryPetLogs.map(buildRewardInventoryItem);
    }, [
        buildRewardInventoryItem,
        inventoryFurniture,
        inventoryPetLogs,
        inventorySupplies,
        inventoryTab,
        t,
    ]);
    const selectedInventoryItem =
        visibleInventoryItems.find((item) => item.key === selectedInventoryKey) ??
        visibleInventoryItems[0] ??
        null;
    const visibleCollectionItems =
        collectionTab === "furniture" ? collectionFurniture : collectionPetLogs;
    const selectedCollectionItem =
        visibleCollectionItems.find((item) => item.reward_key === selectedCollectionKey) ??
        visibleCollectionItems[0] ??
        null;
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
                    <Tooltip content={t("cabin.actions.refresh")} side="bottom">
                        <button
                            type="button"
                            className="cabin-init-icon-button"
                            onClick={() => void refresh()}
                            disabled={refreshing}
                            aria-label={t("cabin.actions.refresh")}
                        >
                            <RefreshCw
                                className={refreshing ? "cabin-init-icon-button__spin" : undefined}
                                aria-hidden="true"
                            />
                        </button>
                    </Tooltip>
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
                    <Tooltip content={t("cabin.actions.inventory")} side="bottom">
                        <button
                            type="button"
                            className="cabin-init-icon-button"
                            onClick={() => setActiveModal("inventory")}
                            aria-label={t("cabin.actions.inventory")}
                        >
                            <Backpack aria-hidden="true" />
                        </button>
                    </Tooltip>
                    <Tooltip content={t("cabin.actions.collection")} side="bottom">
                        <button
                            type="button"
                            className="cabin-init-icon-button"
                            onClick={() => setActiveModal("collection")}
                            aria-label={t("cabin.actions.collection")}
                        >
                            <BookOpen aria-hidden="true" />
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
                <div className="cabin-init-package-list">
                    {pendingPackages.length > 0 ? (
                        pendingPackages.map((item) => (
                            <article className="cabin-init-package" key={item.id}>
                                <div>
                                    <h3>{resolvePackageDisplayText(item, t).title}</h3>
                                    <p>{resolvePackageDisplayText(item, t).description}</p>
                                </div>
                                <div className="cabin-init-package__actions">
                                    <span>
                                        {t("cabin.packages.itemCount", {
                                            count: item.items?.length ?? 0,
                                        })}
                                    </span>
                                    <Button
                                        type="button"
                                        className="cabin-init-package__claim"
                                        loading={claimingPackageId === item.id}
                                        onClick={() => void claimPackage(item.id)}
                                    >
                                        <Check aria-hidden="true" />
                                        {t("cabin.packages.claim")}
                                    </Button>
                                </div>
                            </article>
                        ))
                    ) : (
                        <p className="cabin-init-empty cabin-init-empty--panel">
                            {t("cabin.packages.empty")}
                        </p>
                    )}
                </div>
            </Modal>

            <Modal
                className="cabin-init-modal"
                open={activeModal === "inventory"}
                title={t("cabin.inventory.title")}
                description={t("cabin.inventory.description")}
                closeLabel={t("cabin.modal.close")}
                onClose={() => setActiveModal(null)}
            >
                <div className="cabin-init-tracker">
                    <div className="cabin-init-tracker__tabs" role="tablist">
                        <button
                            type="button"
                            className={
                                inventoryTab === "supplies"
                                    ? "cabin-init-tracker__tab cabin-init-tracker__tab--active"
                                    : "cabin-init-tracker__tab"
                            }
                            onClick={() => setInventoryTab("supplies")}
                            role="tab"
                            aria-selected={inventoryTab === "supplies"}
                        >
                            <Utensils aria-hidden="true" />
                            <span>{t("cabin.inventory.supplies")}</span>
                        </button>
                        <button
                            type="button"
                            className={
                                inventoryTab === "furniture"
                                    ? "cabin-init-tracker__tab cabin-init-tracker__tab--active"
                                    : "cabin-init-tracker__tab"
                            }
                            onClick={() => setInventoryTab("furniture")}
                            role="tab"
                            aria-selected={inventoryTab === "furniture"}
                        >
                            <Armchair aria-hidden="true" />
                            <span>{t("cabin.inventory.furniture")}</span>
                        </button>
                        <button
                            type="button"
                            className={
                                inventoryTab === "petLogs"
                                    ? "cabin-init-tracker__tab cabin-init-tracker__tab--active"
                                    : "cabin-init-tracker__tab"
                            }
                            onClick={() => setInventoryTab("petLogs")}
                            role="tab"
                            aria-selected={inventoryTab === "petLogs"}
                        >
                            <PawPrint aria-hidden="true" />
                            <span>{t("cabin.inventory.petLogs")}</span>
                        </button>
                    </div>

                    {inventoryTab === "supplies" ? (
                        inventorySupplies.length > 0 ? (
                            <div className="cabin-init-tracker__body">
                                {selectedInventoryItem ? (
                                    <section className="cabin-init-tracker__detail cabin-init-tracker__detail--side">
                                        <AssetPreview
                                            assetKey={selectedInventoryItem.assetKey}
                                            alt={selectedInventoryItem.title}
                                            label={selectedInventoryItem.title}
                                            size="lg"
                                        />
                                        <div>
                                            <strong>{selectedInventoryItem.title}</strong>
                                            <span>{selectedInventoryItem.assetKey}</span>
                                        </div>
                                        <p>
                                            {"quantity" in selectedInventoryItem
                                                ? t("cabin.inventory.quantityDetail", {
                                                      quantity: formatNumber(
                                                          selectedInventoryItem.quantity,
                                                      ),
                                                  })
                                                : null}
                                        </p>
                                        <p>{t("cabin.inventory.notPlaceable")}</p>
                                    </section>
                                ) : null}
                                <div className="cabin-init-tracker__grid cabin-init-tracker__grid--scroll">
                                    {visibleInventoryItems.map((item) => (
                                        <button
                                            type="button"
                                            className={[
                                                "cabin-init-tracker__slot",
                                                selectedInventoryItem?.key === item.key
                                                    ? "cabin-init-tracker__slot--selected"
                                                    : "",
                                            ]
                                                .filter(Boolean)
                                                .join(" ")}
                                            onClick={() => setSelectedInventoryKey(item.key)}
                                            key={item.key}
                                            aria-label={item.title}
                                        >
                                            <AssetPreview
                                                assetKey={item.assetKey}
                                                alt=""
                                                label={item.title}
                                            />
                                            {"quantity" in item ? (
                                                <b>{formatNumber(item.quantity)}</b>
                                            ) : null}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <p className="cabin-init-empty">{t("cabin.inventory.emptySupplies")}</p>
                        )
                    ) : null}

                    {inventoryTab === "furniture" ? (
                        inventoryFurniture.length > 0 ? (
                            <div className="cabin-init-tracker__body">
                                {selectedInventoryItem ? (
                                    <section className="cabin-init-tracker__detail cabin-init-tracker__detail--side">
                                        <AssetPreview
                                            assetKey={selectedInventoryItem.assetKey}
                                            alt={selectedInventoryItem.title}
                                            label={selectedInventoryItem.title}
                                            size="lg"
                                        />
                                        <div>
                                            <strong>{selectedInventoryItem.title}</strong>
                                            <span>{selectedInventoryItem.assetKey}</span>
                                        </div>
                                        {"level" in selectedInventoryItem ? (
                                            <>
                                                <p>
                                                    {t("cabin.inventory.rewardDetail", {
                                                        language:
                                                            selectedInventoryItem.sourceLanguage,
                                                        level: selectedInventoryItem.level,
                                                        stage: selectedInventoryItem.stage,
                                                    })}
                                                </p>
                                                <p>
                                                    {selectedInventoryItem.placement
                                                        ? t("cabin.inventory.placed")
                                                        : t("cabin.inventory.notPlaced")}
                                                </p>
                                                <Button
                                                    type="button"
                                                    className="cabin-init-tracker__detail-action"
                                                    disabled={!selectedInventoryItem.placement}
                                                    loading={
                                                        removingPlacementId ===
                                                        selectedInventoryItem.placement?.id
                                                    }
                                                    onClick={() => {
                                                        if (selectedInventoryItem.placement) {
                                                            void removeCabinPlacement(
                                                                selectedInventoryItem.placement.id,
                                                            );
                                                        }
                                                    }}
                                                >
                                                    {t("cabin.inventory.collect")}
                                                </Button>
                                            </>
                                        ) : null}
                                    </section>
                                ) : null}
                                <div className="cabin-init-tracker__grid cabin-init-tracker__grid--scroll">
                                    {visibleInventoryItems.map((item) => (
                                        <button
                                            type="button"
                                            className={[
                                                "cabin-init-tracker__slot",
                                                selectedInventoryItem?.key === item.key
                                                    ? "cabin-init-tracker__slot--selected"
                                                    : "",
                                            ]
                                                .filter(Boolean)
                                                .join(" ")}
                                            onClick={() => setSelectedInventoryKey(item.key)}
                                            key={item.key}
                                            aria-label={item.title}
                                        >
                                            <AssetPreview
                                                assetKey={item.assetKey}
                                                alt=""
                                                label={item.title}
                                            />
                                            {"level" in item ? (
                                                <b>
                                                    {t("cabin.inventory.level", {
                                                        level: item.level,
                                                    })}
                                                </b>
                                            ) : null}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <p className="cabin-init-empty">
                                {t("cabin.inventory.emptyFurniture")}
                            </p>
                        )
                    ) : null}

                    {inventoryTab === "petLogs" ? (
                        inventoryPetLogs.length > 0 ? (
                            <div className="cabin-init-tracker__body">
                                {selectedInventoryItem ? (
                                    <section className="cabin-init-tracker__detail cabin-init-tracker__detail--side">
                                        <AssetPreview
                                            assetKey={selectedInventoryItem.assetKey}
                                            alt={selectedInventoryItem.title}
                                            label={selectedInventoryItem.title}
                                            size="lg"
                                        />
                                        <div>
                                            <strong>{selectedInventoryItem.title}</strong>
                                            <span>{selectedInventoryItem.assetKey}</span>
                                        </div>
                                        {"level" in selectedInventoryItem ? (
                                            <>
                                                <p>
                                                    {t("cabin.inventory.rewardDetail", {
                                                        language:
                                                            selectedInventoryItem.sourceLanguage,
                                                        level: selectedInventoryItem.level,
                                                        stage: selectedInventoryItem.stage,
                                                    })}
                                                </p>
                                                <p>
                                                    {selectedInventoryItem.placement
                                                        ? t("cabin.inventory.placed")
                                                        : t("cabin.inventory.notPlaced")}
                                                </p>
                                                <Button
                                                    type="button"
                                                    className="cabin-init-tracker__detail-action"
                                                    disabled={!selectedInventoryItem.placement}
                                                    loading={
                                                        removingPlacementId ===
                                                        selectedInventoryItem.placement?.id
                                                    }
                                                    onClick={() => {
                                                        if (selectedInventoryItem.placement) {
                                                            void removeCabinPlacement(
                                                                selectedInventoryItem.placement.id,
                                                            );
                                                        }
                                                    }}
                                                >
                                                    {t("cabin.inventory.collect")}
                                                </Button>
                                            </>
                                        ) : null}
                                    </section>
                                ) : null}
                                <div className="cabin-init-tracker__grid cabin-init-tracker__grid--scroll">
                                    {visibleInventoryItems.map((item) => (
                                        <button
                                            type="button"
                                            className={[
                                                "cabin-init-tracker__slot",
                                                selectedInventoryItem?.key === item.key
                                                    ? "cabin-init-tracker__slot--selected"
                                                    : "",
                                            ]
                                                .filter(Boolean)
                                                .join(" ")}
                                            onClick={() => setSelectedInventoryKey(item.key)}
                                            key={item.key}
                                            aria-label={item.title}
                                        >
                                            <AssetPreview
                                                assetKey={item.assetKey}
                                                alt=""
                                                label={item.title}
                                            />
                                            {"stage" in item ? (
                                                <b>
                                                    {t("cabin.inventory.stage", {
                                                        stage: item.stage,
                                                    })}
                                                </b>
                                            ) : null}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <p className="cabin-init-empty">{t("cabin.inventory.emptyPetLogs")}</p>
                        )
                    ) : null}
                </div>
            </Modal>

            <Modal
                className="cabin-init-modal"
                open={activeModal === "collection"}
                title={t("cabin.collection.title")}
                description={t("cabin.collection.description")}
                closeLabel={t("cabin.modal.close")}
                onClose={() => setActiveModal(null)}
            >
                <div className="cabin-init-tracker">
                    <div className="cabin-init-tracker__tabs" role="tablist">
                        <button
                            type="button"
                            className={
                                collectionTab === "furniture"
                                    ? "cabin-init-tracker__tab cabin-init-tracker__tab--active"
                                    : "cabin-init-tracker__tab"
                            }
                            onClick={() => setCollectionTab("furniture")}
                            role="tab"
                            aria-selected={collectionTab === "furniture"}
                        >
                            <Armchair aria-hidden="true" />
                            <span>{t("cabin.collection.furniture")}</span>
                        </button>
                        <button
                            type="button"
                            className={
                                collectionTab === "petLogs"
                                    ? "cabin-init-tracker__tab cabin-init-tracker__tab--active"
                                    : "cabin-init-tracker__tab"
                            }
                            onClick={() => setCollectionTab("petLogs")}
                            role="tab"
                            aria-selected={collectionTab === "petLogs"}
                        >
                            <PawPrint aria-hidden="true" />
                            <span>{t("cabin.collection.petLogs")}</span>
                        </button>
                    </div>

                    <div className="cabin-init-tracker__body">
                        {selectedCollectionItem ? (
                            <section className="cabin-init-tracker__detail cabin-init-tracker__detail--side">
                                <AssetPreview
                                    assetKey={selectedCollectionItem.asset_key}
                                    alt={resolveRewardName(
                                        selectedCollectionItem.reward_key,
                                        selectedCollectionItem.source_language,
                                        t,
                                    )}
                                    label={resolveRewardName(
                                        selectedCollectionItem.reward_key,
                                        selectedCollectionItem.source_language,
                                        t,
                                    )}
                                    size="lg"
                                />
                                <div>
                                    <strong>
                                        {resolveRewardName(
                                            selectedCollectionItem.reward_key,
                                            selectedCollectionItem.source_language,
                                            t,
                                        )}
                                    </strong>
                                    <span>{selectedCollectionItem.asset_key}</span>
                                </div>
                                <p>
                                    {selectedCollectionItem.owned
                                        ? t("cabin.collection.ownedDetail", {
                                              language: selectedCollectionItem.source_language,
                                              level: selectedCollectionItem.stack_reward_level,
                                          })
                                        : getCollectionRequirementText(selectedCollectionItem, t)}
                                </p>
                            </section>
                        ) : null}
                        {collectionTab === "furniture" ? (
                            <div className="cabin-init-tracker__grid cabin-init-tracker__grid--scroll">
                                {collectionFurniture.map((item) => (
                                    <button
                                        type="button"
                                        className={[
                                            "cabin-init-tracker__slot",
                                            item.owned ? "" : "cabin-init-tracker__slot--locked",
                                            selectedCollectionItem?.reward_key === item.reward_key
                                                ? "cabin-init-tracker__slot--selected"
                                                : "",
                                        ]
                                            .filter(Boolean)
                                            .join(" ")}
                                        onClick={() => setSelectedCollectionKey(item.reward_key)}
                                        key={item.reward_key}
                                        aria-label={`${item.owned ? resolveRewardName(item.reward_key, item.source_language, t) : t("cabin.collection.unknown")}${item.source_language}${item.owned ? t("cabin.collection.owned") : t("cabin.collection.locked", { level: item.mastery_level })}`}
                                    >
                                        <AssetPreview
                                            assetKey={item.asset_key}
                                            alt=""
                                            label={
                                                item.owned
                                                    ? resolveRewardName(
                                                          item.reward_key,
                                                          item.source_language,
                                                          t,
                                                      )
                                                    : t("cabin.collection.unknown")
                                            }
                                        />
                                        <b>
                                            {item.owned
                                                ? t("cabin.collection.owned")
                                                : t("cabin.collection.locked", {
                                                      level: item.mastery_level,
                                                  })}
                                        </b>
                                    </button>
                                ))}
                            </div>
                        ) : null}

                        {collectionTab === "petLogs" ? (
                            <div className="cabin-init-tracker__grid cabin-init-tracker__grid--scroll">
                                {collectionPetLogs.map((item) => (
                                    <button
                                        type="button"
                                        className={[
                                            "cabin-init-tracker__slot",
                                            item.owned ? "" : "cabin-init-tracker__slot--locked",
                                            selectedCollectionItem?.reward_key === item.reward_key
                                                ? "cabin-init-tracker__slot--selected"
                                                : "",
                                        ]
                                            .filter(Boolean)
                                            .join(" ")}
                                        onClick={() => setSelectedCollectionKey(item.reward_key)}
                                        key={item.reward_key}
                                        aria-label={`${item.owned ? resolveRewardName(item.reward_key, item.source_language, t) : t("cabin.collection.unknown")}${item.source_language}${item.owned ? t("cabin.collection.owned") : t("cabin.collection.locked", { level: item.mastery_level })}`}
                                    >
                                        <AssetPreview
                                            assetKey={item.asset_key}
                                            alt=""
                                            label={
                                                item.owned
                                                    ? resolveRewardName(
                                                          item.reward_key,
                                                          item.source_language,
                                                          t,
                                                      )
                                                    : t("cabin.collection.unknown")
                                            }
                                        />
                                        <b>
                                            {item.owned
                                                ? t("cabin.collection.owned")
                                                : t("cabin.collection.locked", {
                                                      level: item.mastery_level,
                                                  })}
                                        </b>
                                    </button>
                                ))}
                            </div>
                        ) : null}
                    </div>
                </div>
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
