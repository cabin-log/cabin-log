import { Code2, SlidersHorizontal, UserRound } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { ConnectedOAuthProvidersCard } from "../../components/features/auth/ConnectedOAuthProvidersCard";
import { DeveloperApiKeysSection } from "../../components/features/apiKey/DeveloperApiKeysSection";
import {
    AvatarUploadField,
    Button,
    DropdownMenu,
    InlineMessage,
    InputField,
    MenuList,
    PrimaryCard,
    StatusBadge,
    UserAvatar,
} from "../../components/ui";
import { useApiKeyApi, type APIKeyRecord } from "../../hooks/api/apiKey/useApiKeyApi";
import { useApiKeyRealtimeSubscription } from "../../hooks/realtime/apiKey/useApiKeyRealtimeSubscription";
import { useAuthContext } from "../../hooks/useAuth";
import { useAppConfig } from "../../hooks/useFeatures";
import { resolveAPIKeyExpiresAt, type APIKeyExpiryOption } from "../../utils/date";

type SaveFeedback = {
    message: string;
    tone: "error" | "info";
    source: "name" | "photo";
} | null;
type SettingsMenuKey = "profile" | "general" | "developers";
const MAX_PROFILE_PHOTO_SIZE_MB = 8;
const MAX_PROFILE_PHOTO_SIZE_BYTES = MAX_PROFILE_PHOTO_SIZE_MB * 1024 * 1024;
const DEFAULT_API_KEY_EXPIRY_OPTION: APIKeyExpiryOption = "30d";
const SUPPORTED_LANGUAGE_IDS = ["en", "ko"] as const;
type SupportedLanguageId = (typeof SUPPORTED_LANGUAGE_IDS)[number];

export function SettingsPage() {
    const { t, i18n } = useTranslation();
    const { user, updateProfile } = useAuthContext();
    const {
        createApiKey,
        deleteApiKey,
        listApiKeys,
        updateApiKeyStatus,
        extractAPIKeyErrorDetail,
        resolveAPIKeyErrorMessage,
    } = useApiKeyApi();
    const { data: appConfig } = useAppConfig();
    const [activeMenu, setActiveMenu] = useState<SettingsMenuKey>("profile");
    const [nameInput, setNameInput] = useState("");
    const [profileImageInput, setProfileImageInput] = useState<string | null>(null);
    const [saveBusy, setSaveBusy] = useState(false);
    const [saveFeedback, setSaveFeedback] = useState<SaveFeedback>(null);
    const [apiKeyItems, setApiKeyItems] = useState<APIKeyRecord[]>([]);
    const [apiKeyLoading, setApiKeyLoading] = useState(true);
    const [apiKeyErrorMessage, setApiKeyErrorMessage] = useState<string | null>(null);
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [newApiKeyName, setNewApiKeyName] = useState("");
    const [newApiKeyExpiryOption, setNewApiKeyExpiryOption] = useState<APIKeyExpiryOption>(
        DEFAULT_API_KEY_EXPIRY_OPTION,
    );
    const [createBusy, setCreateBusy] = useState(false);
    const [createErrorMessage, setCreateErrorMessage] = useState<string | null>(null);
    const [createdSecret, setCreatedSecret] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);
    const [deactivateTarget, setDeactivateTarget] = useState<APIKeyRecord | null>(null);
    const [deactivateBusy, setDeactivateBusy] = useState(false);
    const [toggleBusyId, setToggleBusyId] = useState<number | null>(null);
    const loginEnabled = appConfig?.login_enabled === true;

    const showProfile = activeMenu === "profile";
    const showDevelopers = activeMenu === "developers";
    const HeaderIcon = showProfile ? UserRound : showDevelopers ? Code2 : SlidersHorizontal;
    const settingsMenuItems = [
        { key: "profile", label: t("settings.menu.profile"), icon: UserRound },
        { key: "general", label: t("settings.menu.general"), icon: SlidersHorizontal },
        { key: "developers", label: t("settings.menu.developers"), icon: Code2 },
    ] as const;
    const normalizedNameInput = nameInput.trim();
    const normalizedCurrentName = (user?.name ?? "").trim();
    const normalizedProfileImageInput = profileImageInput?.trim() || null;
    const normalizedCurrentProfileImage = user?.profile_image_url ?? null;
    const isNameChanged = normalizedNameInput !== normalizedCurrentName;
    const connectedOAuthProviders = user?.oauth_providers ?? [];
    const normalizedLanguageId =
        (i18n.resolvedLanguage ?? i18n.language ?? "en").split("-")[0] || "en";
    const currentLanguageId: SupportedLanguageId = SUPPORTED_LANGUAGE_IDS.includes(
        normalizedLanguageId as SupportedLanguageId,
    )
        ? (normalizedLanguageId as SupportedLanguageId)
        : "en";
    const currentLanguageLabel = t(`settings.general.languages.${currentLanguageId}`);
    const isAdminUser = user?.role === "admin";

    const resolveOAuthProviderLabel = (provider: string) => {
        if (provider === "google") {
            return t("settings.profile.oauthProviders.google");
        }
        if (provider === "github") {
            return t("settings.profile.oauthProviders.github");
        }
        return provider.toUpperCase();
    };
    const resolveApiKeyErrorMessage = useCallback(
        (error: unknown, fallbackKey: string) => {
            const detail = extractAPIKeyErrorDetail(error);
            return resolveAPIKeyErrorMessage(t, detail, fallbackKey);
        },
        [extractAPIKeyErrorDetail, resolveAPIKeyErrorMessage, t],
    );

    const loadApiKeys = useCallback(async () => {
        setApiKeyLoading(true);
        setApiKeyErrorMessage(null);
        try {
            const response = await listApiKeys();
            setApiKeyItems(response.items);
        } catch (nextError) {
            setApiKeyErrorMessage(
                resolveApiKeyErrorMessage(nextError, "settings.developers.listLoadError"),
            );
        } finally {
            setApiKeyLoading(false);
        }
    }, [listApiKeys, resolveApiKeyErrorMessage]);

    const openCreateModal = useCallback(() => {
        setCreateModalOpen(true);
        setCreateErrorMessage(null);
    }, []);

    const closeCreateModal = useCallback(() => {
        if (createBusy) {
            return;
        }
        setCreateModalOpen(false);
        setNewApiKeyName("");
        setNewApiKeyExpiryOption(DEFAULT_API_KEY_EXPIRY_OPTION);
        setCreateErrorMessage(null);
    }, [createBusy]);

    const handleToggleStatus = useCallback(
        (apiKeyId: number, enabled: boolean) => {
            setToggleBusyId(apiKeyId);
            setApiKeyErrorMessage(null);
            void updateApiKeyStatus(apiKeyId, enabled)
                .then((updated) => {
                    setApiKeyItems((prev) =>
                        prev.map((row) => (row.id === updated.id ? updated : row)),
                    );
                })
                .catch((nextError) => {
                    setApiKeyErrorMessage(
                        resolveApiKeyErrorMessage(nextError, "settings.developers.updateError"),
                    );
                })
                .finally(() => {
                    setToggleBusyId(null);
                });
        },
        [resolveApiKeyErrorMessage, updateApiKeyStatus],
    );

    const handleCreateApiKey = useCallback(() => {
        const trimmedName = newApiKeyName.trim();
        if (!trimmedName) {
            return;
        }

        setCreateBusy(true);
        setCreateErrorMessage(null);
        void createApiKey(trimmedName, resolveAPIKeyExpiresAt(newApiKeyExpiryOption))
            .then((result) => {
                setApiKeyItems((prev) => [result.key, ...prev]);
                setCreateModalOpen(false);
                setNewApiKeyName("");
                setNewApiKeyExpiryOption(DEFAULT_API_KEY_EXPIRY_OPTION);
                setCreateErrorMessage(null);
                setCreatedSecret(result.api_key);
                setCopied(false);
            })
            .catch((nextError) => {
                setCreateErrorMessage(
                    resolveApiKeyErrorMessage(nextError, "settings.developers.createError"),
                );
            })
            .finally(() => {
                setCreateBusy(false);
            });
    }, [createApiKey, newApiKeyExpiryOption, newApiKeyName, resolveApiKeyErrorMessage]);

    const closeSecretModal = useCallback(() => {
        setCreatedSecret(null);
        setCopied(false);
    }, []);

    const copySecret = useCallback(() => {
        if (!createdSecret) {
            return;
        }
        void navigator.clipboard.writeText(createdSecret).then(() => {
            setCopied(true);
        });
    }, [createdSecret]);

    const closeDeleteModal = useCallback(() => {
        if (deactivateBusy) {
            return;
        }
        setDeactivateTarget(null);
    }, [deactivateBusy]);

    const confirmDelete = useCallback(() => {
        if (!deactivateTarget) {
            return;
        }
        setDeactivateBusy(true);
        setApiKeyErrorMessage(null);
        void deleteApiKey(deactivateTarget.id)
            .then((deleted) => {
                setApiKeyItems((prev) => prev.filter((item) => item.id !== deleted.id));
                setDeactivateTarget(null);
            })
            .catch((nextError) => {
                setApiKeyErrorMessage(
                    resolveApiKeyErrorMessage(nextError, "settings.developers.deactivateError"),
                );
            })
            .finally(() => {
                setDeactivateBusy(false);
            });
    }, [deactivateTarget, deleteApiKey, resolveApiKeyErrorMessage]);

    useEffect(() => {
        setNameInput(user?.name ?? "");
        setProfileImageInput(user?.profile_image_url ?? null);
    }, [user?.name, user?.profile_image_url]);

    useEffect(() => {
        setSaveFeedback(null);
        setNameInput(user?.name ?? "");
        setProfileImageInput(user?.profile_image_url ?? null);
    }, [activeMenu]);

    useEffect(() => {
        void loadApiKeys();
    }, [loadApiKeys]);

    const handleRealtimeAPIKeyCreated = useCallback((created: APIKeyRecord) => {
        const id = created.id;
        setApiKeyItems((prev) => {
            if (prev.some((item) => item.id === id)) {
                return prev.map((item) => (item.id === id ? created : item));
            }
            return [created, ...prev];
        });
    }, []);

    const handleRealtimeAPIKeyStatusUpdated = useCallback((updated: APIKeyRecord) => {
        const id = updated.id;
        setApiKeyItems((prev) => prev.map((item) => (item.id === id ? updated : item)));
    }, []);

    const handleRealtimeAPIKeyDeleted = useCallback((deleted: APIKeyRecord) => {
        const id = deleted.id;
        setApiKeyItems((prev) => prev.filter((item) => item.id !== id));
    }, []);

    useApiKeyRealtimeSubscription({
        enabled: loginEnabled && showDevelopers,
        onCreated: handleRealtimeAPIKeyCreated,
        onStatusUpdated: handleRealtimeAPIKeyStatusUpdated,
        onDeleted: handleRealtimeAPIKeyDeleted,
    });

    const toDataUrl = (file: File): Promise<string> =>
        new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                if (typeof reader.result === "string") {
                    resolve(reader.result);
                    return;
                }
                reject(new Error("Failed to read image file."));
            };
            reader.onerror = () => reject(new Error("Failed to read image file."));
            reader.readAsDataURL(file);
        });

    const handleProfileImageSelect = async (file: File | null) => {
        if (!file) {
            return;
        }

        setSaveFeedback(null);
        const isSupportedType = [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp",
            "image/gif",
        ].includes(file.type);
        if (!isSupportedType) {
            setSaveFeedback({
                tone: "error",
                source: "photo",
                message: t("settings.profile.photoTypeError"),
            });
            return;
        }
        if (file.size > MAX_PROFILE_PHOTO_SIZE_BYTES) {
            setSaveFeedback({
                tone: "error",
                source: "photo",
                message: t("settings.profile.photoSizeError"),
            });
            return;
        }

        try {
            const dataUrl = await toDataUrl(file);
            setProfileImageInput(dataUrl);
            setSaveBusy(true);
            try {
                await updateProfile({ profile_image_url: dataUrl });
                setSaveFeedback(null);
            } catch {
                setProfileImageInput(normalizedCurrentProfileImage);
                setSaveFeedback(null);
            } finally {
                setSaveBusy(false);
            }
        } catch {
            setSaveFeedback({
                tone: "error",
                source: "photo",
                message: t("settings.profile.photoReadError"),
            });
        }
    };

    const handleSaveProfile = async () => {
        const nextName = normalizedNameInput;
        if (!isNameChanged || !nextName) {
            return;
        }

        setSaveBusy(true);
        setSaveFeedback(null);
        try {
            await updateProfile({ name: nextName });
            setSaveFeedback({
                tone: "info",
                source: "name",
                message: t("settings.profile.nameSaveSuccess"),
            });
        } catch (error) {
            setSaveFeedback({
                tone: "error",
                source: "name",
                message: t("settings.profile.nameSaveError"),
            });
        } finally {
            setSaveBusy(false);
        }
    };

    return (
        <section className="settings-layout">
            <MenuList
                items={settingsMenuItems}
                activeKey={activeMenu}
                onSelect={setActiveMenu}
                ariaLabel={t("settings.menu.title")}
            />

            <PrimaryCard className="settings-content-card">
                {showProfile ? (
                    <>
                        <header className="settings-content-card__header">
                            <h1>
                                <span
                                    className="settings-content-card__title-icon"
                                    aria-hidden="true"
                                >
                                    <HeaderIcon />
                                </span>
                                <span>{t("settings.profile.title")}</span>
                            </h1>
                            <p>{t("settings.profile.subtitle")}</p>
                            {isAdminUser ? (
                                <div className="settings-profile-role-badge-wrap">
                                    <StatusBadge tone="active">
                                        {t("settings.profile.roleBadgeAdmin")}
                                    </StatusBadge>
                                </div>
                            ) : null}
                        </header>

                        <section
                            className="settings-profile-content"
                            aria-label={t("settings.profile.title")}
                        >
                            <div className="settings-profile-info">
                                <article className="settings-profile-field-card">
                                    <h2>{t("settings.labels.name")}</h2>
                                    <form
                                        className="settings-profile-name-edit"
                                        onSubmit={(event) => {
                                            event.preventDefault();
                                            void handleSaveProfile();
                                        }}
                                    >
                                        <InputField
                                            className="settings-profile-name-input"
                                            label=""
                                            value={nameInput}
                                            onValueChange={(value) => {
                                                setNameInput(value);
                                                if (saveFeedback) {
                                                    setSaveFeedback(null);
                                                }
                                            }}
                                            placeholder={t("settings.profile.namePlaceholder")}
                                            aria-label={t("settings.labels.name")}
                                        />
                                        <Button
                                            className="settings-profile-save-button"
                                            type="submit"
                                            loading={saveBusy}
                                            disabled={!isNameChanged}
                                        >
                                            {t("settings.profile.save")}
                                        </Button>
                                    </form>
                                    <div className="settings-feedback-slot settings-feedback-slot--name">
                                        {saveFeedback?.source === "name" &&
                                        saveFeedback?.tone === "info" ? (
                                            <div className="settings-feedback settings-feedback--name">
                                                <InlineMessage tone="info">
                                                    {saveFeedback.message}
                                                </InlineMessage>
                                            </div>
                                        ) : null}
                                        {saveFeedback?.source === "name" &&
                                        saveFeedback?.tone === "error" ? (
                                            <div className="settings-feedback settings-feedback--name">
                                                <InlineMessage>
                                                    {saveFeedback.message}
                                                </InlineMessage>
                                            </div>
                                        ) : null}
                                    </div>
                                </article>

                                <article className="settings-profile-field-card">
                                    <h2>{t("settings.labels.email")}</h2>
                                    <p>{user?.email ?? "-"}</p>
                                </article>

                                {loginEnabled ? (
                                    <ConnectedOAuthProvidersCard
                                        title={t("settings.profile.oauthConnectedTitle")}
                                        providers={connectedOAuthProviders}
                                        emptyText={t("settings.profile.oauthConnectedEmpty")}
                                        getProviderLabel={resolveOAuthProviderLabel}
                                    />
                                ) : null}
                            </div>

                            <aside className="settings-profile-photo-panel">
                                <h2>{t("settings.profile.photo")}</h2>
                                <UserAvatar
                                    className="settings-profile-photo-card__preview"
                                    imageUrl={normalizedProfileImageInput}
                                    label={user?.name ?? "U"}
                                />
                                <AvatarUploadField
                                    busy={saveBusy}
                                    canClear={Boolean(normalizedProfileImageInput)}
                                    helperText={t("settings.profile.photoHelp")}
                                    selectButtonText={t("settings.profile.photoSelect")}
                                    clearButtonText={t("settings.profile.photoClear")}
                                    onSelectFile={(file) => {
                                        void handleProfileImageSelect(file);
                                    }}
                                    onClear={() => {
                                        setProfileImageInput(null);
                                        if (saveFeedback) {
                                            setSaveFeedback(null);
                                        }
                                        setSaveBusy(true);
                                        void updateProfile({ profile_image_url: null })
                                            .then(() => {
                                                setSaveFeedback(null);
                                            })
                                            .catch(() => {
                                                setProfileImageInput(normalizedCurrentProfileImage);
                                                setSaveFeedback(null);
                                            })
                                            .finally(() => {
                                                setSaveBusy(false);
                                            });
                                    }}
                                />
                            </aside>
                        </section>
                    </>
                ) : showDevelopers ? (
                    <>
                        <header className="settings-content-card__header">
                            <h1>
                                <span
                                    className="settings-content-card__title-icon"
                                    aria-hidden="true"
                                >
                                    <HeaderIcon />
                                </span>
                                <span>{t("settings.developers.title")}</span>
                            </h1>
                            <p>{t("settings.developers.subtitle")}</p>
                        </header>
                        <section
                            className="settings-general-content"
                            aria-label={t("settings.developers.title")}
                        >
                            <DeveloperApiKeysSection
                                controller={{
                                    items: apiKeyItems,
                                    loading: apiKeyLoading,
                                    errorMessage: apiKeyErrorMessage,
                                    createModalOpen,
                                    newApiKeyName,
                                    newApiKeyExpiryOption,
                                    createBusy,
                                    createErrorMessage,
                                    createdSecret,
                                    copied,
                                    deactivateTarget,
                                    deactivateBusy,
                                    toggleBusyId,
                                    setNewApiKeyName,
                                    setNewApiKeyExpiryOption,
                                    openCreateModal,
                                    closeCreateModal,
                                    handleCreateApiKey,
                                    handleToggleStatus,
                                    setDeactivateTarget,
                                    closeDeleteModal,
                                    confirmDelete,
                                    closeSecretModal,
                                    copySecret,
                                }}
                            />
                        </section>
                    </>
                ) : (
                    <>
                        <header className="settings-content-card__header">
                            <h1>
                                <span
                                    className="settings-content-card__title-icon"
                                    aria-hidden="true"
                                >
                                    <HeaderIcon />
                                </span>
                                <span>{t("settings.general.title")}</span>
                            </h1>
                            <p>{t("settings.general.subtitle")}</p>
                        </header>
                        <section
                            className="settings-general-content"
                            aria-label={t("settings.general.title")}
                        >
                            <article className="settings-profile-field-card">
                                <h2>{t("settings.general.languageTitle")}</h2>
                                <div className="settings-general-control">
                                    <DropdownMenu
                                        triggerLabel={currentLanguageLabel}
                                        label={t("settings.general.languageTitle")}
                                        items={SUPPORTED_LANGUAGE_IDS.map((languageId) => ({
                                            id: languageId,
                                            label: t(`settings.general.languages.${languageId}`),
                                        }))}
                                        onSelect={(languageId) => {
                                            void i18n.changeLanguage(languageId);
                                        }}
                                    />
                                </div>
                            </article>
                        </section>
                    </>
                )}
            </PrimaryCard>
        </section>
    );
}
