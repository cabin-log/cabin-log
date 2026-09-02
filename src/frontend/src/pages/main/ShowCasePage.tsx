import { useTranslation } from "react-i18next";
import { KeyRound, SlidersHorizontal, UserRound } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import { ErrorCard, InfoCard, WarningCard } from "../../components/ui/status/StatusCard";
import { OAuthOptionsCard } from "../../components/features/auth/OAuthOptionsCard";
import { OAuthProviderButton } from "../../components/features/auth/OAuthProviderButton";
import {
    BrandMark,
    Button,
    DropdownMenu,
    FormCheckbox,
    InlineMessage,
    InputField,
    KeyValueCard,
    MenuList,
    Modal,
    ModalButton,
    Pagination,
    PanelCard,
    Spinner,
    StatusBadge,
    Tooltip,
    ToggleSwitch,
    ValidationCard,
} from "../../components/ui";
import { useAuthContext } from "../../hooks/useAuth";

function ShowcaseItem({
    component,
    children,
    className,
}: {
    component: string;
    children: ReactNode;
    className?: string;
}) {
    const nextClassName = className ? `showcase-item ${className}` : "showcase-item";
    return (
        <div className={nextClassName} data-component={component}>
            <p className="showcase-item__name">{component}</p>
            <div className="showcase-item__preview">{children}</div>
        </div>
    );
}

export function ShowCasePage() {
    const { t } = useTranslation();
    const { user } = useAuthContext();
    const navigate = useNavigate();
    const [sampleInput, setSampleInput] = useState("");
    const [sampleChecked, setSampleChecked] = useState(true);
    const [sampleUnchecked, setSampleUnchecked] = useState(false);
    const [sampleMenu, setSampleMenu] = useState("profile");
    const [sampleToggle, setSampleToggle] = useState(true);
    const [sampleModalOpen, setSampleModalOpen] = useState(false);
    const [sampleCardPage, setSampleCardPage] = useState(1);
    const sampleCards = Array.from({ length: 13 }, (_, index) => ({
        id: index + 1,
        title: `Card ${index + 1}`,
        meta: `Sample item ${String(index + 1).padStart(2, "0")}`,
    }));
    const sampleCardPageSize = 6;
    const sampleCardTotalPages = Math.ceil(sampleCards.length / sampleCardPageSize);
    const sampleCardStartIndex = (sampleCardPage - 1) * sampleCardPageSize;
    const visibleSampleCards = sampleCards.slice(
        sampleCardStartIndex,
        sampleCardStartIndex + sampleCardPageSize,
    );
    const sampleCardPlaceholderCount = Math.max(0, sampleCardPageSize - visibleSampleCards.length);
    const sampleMenuItems = [
        { key: "profile", label: "Profile", icon: UserRound },
        { key: "general", label: "General", icon: SlidersHorizontal },
        { key: "apiKey", label: "API Key", icon: KeyRound },
    ];

    return (
        <section className="showcase-catalog">
            <header className="showcase-catalog__header">
                <h1>{t("showCase.title")}</h1>
                <p>{t("showCase.subtitle")}</p>
            </header>

            <section className="showcase-catalog__group">
                <h2>Buttons & Components</h2>
                <div className="showcase-catalog__components">
                    <div className="showcase-catalog__section-card">
                        <h3>Brand</h3>
                        <div className="showcase-catalog__row">
                            <ShowcaseItem component="BrandMark">
                                <BrandMark />
                            </ShowcaseItem>
                        </div>
                    </div>

                    <div className="showcase-catalog__section-card">
                        <h3>Buttons</h3>
                        <div className="showcase-catalog__row">
                            <ShowcaseItem component="Button">
                                <Button>Primary button</Button>
                            </ShowcaseItem>
                            <ShowcaseItem component="Button (loading)">
                                <Button loading>Loading button</Button>
                            </ShowcaseItem>
                            <ShowcaseItem component="Button (disabled)">
                                <Button disabled>Disabled button</Button>
                            </ShowcaseItem>
                            <ShowcaseItem component="OAuthProviderButton (google/github)">
                                <div className="showcase-catalog__oauth-row">
                                    <OAuthProviderButton
                                        provider="google"
                                        label="Continue with Google"
                                        startPath="/show-case"
                                    />
                                    <OAuthProviderButton
                                        provider="github"
                                        label="Continue with GitHub"
                                        startPath="/show-case"
                                    />
                                </div>
                            </ShowcaseItem>
                        </div>
                    </div>

                    <div className="showcase-catalog__section-card">
                        <h3>Dropdown</h3>
                        <div className="showcase-catalog__row">
                            <ShowcaseItem component="DropdownMenu">
                                <DropdownMenu
                                    triggerLabel="Open menu"
                                    label="Demo dropdown"
                                    items={[
                                        { id: "item-1", label: "Item 1" },
                                        { id: "item-2", label: "Item 2" },
                                        { id: "item-3", label: "Item 3" },
                                    ]}
                                />
                            </ShowcaseItem>
                            <ShowcaseItem component="Tooltip">
                                <Tooltip content={t("showCase.tooltip.demoContent")} side="top">
                                    <Button type="button">
                                        {t("showCase.tooltip.demoTrigger")}
                                    </Button>
                                </Tooltip>
                            </ShowcaseItem>
                        </div>
                    </div>

                    <div className="showcase-catalog__section-card">
                        <h3>Menu</h3>
                        <div className="showcase-catalog__row">
                            <ShowcaseItem component="MenuList">
                                <MenuList
                                    items={sampleMenuItems}
                                    activeKey={sampleMenu}
                                    onSelect={setSampleMenu}
                                    ariaLabel="Sample menu list"
                                />
                            </ShowcaseItem>
                        </div>
                    </div>

                    <div className="showcase-catalog__section-card">
                        <h3>Inputs</h3>
                        <div className="showcase-catalog__stack">
                            <ShowcaseItem component="InputField">
                                <InputField
                                    label="Sample input"
                                    value={sampleInput}
                                    onValueChange={setSampleInput}
                                    placeholder="Type something..."
                                />
                            </ShowcaseItem>
                            <div className="showcase-catalog__row">
                                <ShowcaseItem component="FormCheckbox (checked)">
                                    <FormCheckbox
                                        checked={sampleChecked}
                                        onCheckedChange={setSampleChecked}
                                        label="Checked checkbox"
                                    />
                                </ShowcaseItem>
                                <ShowcaseItem component="FormCheckbox (unchecked)">
                                    <FormCheckbox
                                        checked={sampleUnchecked}
                                        onCheckedChange={setSampleUnchecked}
                                        label="Unchecked checkbox"
                                    />
                                </ShowcaseItem>
                            </div>
                            <ShowcaseItem component="ToggleSwitch">
                                <ToggleSwitch
                                    checked={sampleToggle}
                                    onCheckedChange={setSampleToggle}
                                    label="Active key"
                                />
                            </ShowcaseItem>
                        </div>
                    </div>

                    <div className="showcase-catalog__section-card">
                        <h3>Data Views</h3>
                        <div className="showcase-catalog__stack">
                            <ShowcaseItem component="StatusBadge">
                                <div className="showcase-catalog__badge-row">
                                    <StatusBadge tone="active">Active</StatusBadge>
                                    <StatusBadge tone="inactive">Inactive</StatusBadge>
                                    <StatusBadge tone="info">Info</StatusBadge>
                                </div>
                            </ShowcaseItem>
                            <ShowcaseItem component="InlineMessage">
                                <div className="showcase-catalog__stack">
                                    <InlineMessage tone="info">
                                        Name updated successfully.
                                    </InlineMessage>
                                    <InlineMessage>
                                        Failed to update your profile. Please try again.
                                    </InlineMessage>
                                </div>
                            </ShowcaseItem>
                            <ShowcaseItem
                                component="Card list + Pagination"
                                className="showcase-catalog__paginated-card-demo"
                            >
                                <div className="showcase-paginated-cards">
                                    <div className="showcase-paginated-cards__grid">
                                        {visibleSampleCards.map((item) => (
                                            <article
                                                key={item.id}
                                                className="showcase-paginated-card"
                                            >
                                                <h4>{item.title}</h4>
                                                <p>{item.meta}</p>
                                            </article>
                                        ))}
                                        {Array.from(
                                            { length: sampleCardPlaceholderCount },
                                            (_, index) => (
                                                <article
                                                    key={`placeholder-${index}`}
                                                    className="showcase-paginated-card showcase-paginated-card--placeholder"
                                                    aria-hidden="true"
                                                />
                                            ),
                                        )}
                                    </div>
                                    <Pagination
                                        currentPage={sampleCardPage}
                                        totalPages={sampleCardTotalPages}
                                        ariaLabel="Pagination"
                                        previousLabel="Previous page"
                                        nextLabel="Next page"
                                        onPageChange={setSampleCardPage}
                                    />
                                </div>
                            </ShowcaseItem>
                        </div>
                    </div>

                    <div className="showcase-catalog__section-card">
                        <h3>Modal</h3>
                        <div className="showcase-catalog__row">
                            <ShowcaseItem component="Modal + ModalButton">
                                <ModalButton
                                    variant="save"
                                    onClick={() => {
                                        setSampleModalOpen(true);
                                    }}
                                >
                                    Open modal
                                </ModalButton>
                                <Modal
                                    open={sampleModalOpen}
                                    title="Sample modal"
                                    description="Reusable modal with modal buttons."
                                    onClose={() => {
                                        setSampleModalOpen(false);
                                    }}
                                    footer={
                                        <>
                                            <ModalButton
                                                variant="cancel"
                                                onClick={() => {
                                                    setSampleModalOpen(false);
                                                }}
                                            >
                                                Cancel
                                            </ModalButton>
                                            <ModalButton
                                                variant="save"
                                                onClick={() => {
                                                    setSampleModalOpen(false);
                                                }}
                                            >
                                                Save
                                            </ModalButton>
                                        </>
                                    }
                                >
                                    <p className="muted">This is a modal body content sample.</p>
                                </Modal>
                            </ShowcaseItem>
                        </div>
                    </div>

                    <div className="showcase-catalog__section-card">
                        <h3>Spinners</h3>
                        <div className="showcase-catalog__row">
                            <ShowcaseItem component="Spinner (sm)">
                                <Spinner size="sm" label="Small spinner" />
                            </ShowcaseItem>
                            <ShowcaseItem component="Spinner (md)">
                                <Spinner size="md" label="Medium spinner" />
                            </ShowcaseItem>
                            <ShowcaseItem component="Spinner (lg)">
                                <Spinner size="lg" label="Large spinner" />
                            </ShowcaseItem>
                        </div>
                    </div>

                    <div className="showcase-catalog__section-card">
                        <h3>Pages</h3>
                        <div className="showcase-catalog__row">
                            <ShowcaseItem component="LoadingPage">
                                <Button
                                    type="button"
                                    onClick={() => navigate("/show-case/loading")}
                                >
                                    Open loading page
                                </Button>
                            </ShowcaseItem>
                            <ShowcaseItem component="ShowCaseNotFoundPage">
                                <Button type="button" onClick={() => navigate("/show-case/404")}>
                                    Open 404 page
                                </Button>
                            </ShowcaseItem>
                        </div>
                    </div>
                </div>
            </section>

            <section className="showcase-catalog__group">
                <h2>Cards</h2>
                <div className="showcase-catalog__cards">
                    <ShowcaseItem component="PanelCard" className="showcase-catalog__panel-demo">
                        <PanelCard
                            title="Panel Card"
                            subtitle="Generic container card used across auth screens."
                        >
                            <p className="muted">Reusable top-level card sample.</p>
                        </PanelCard>
                    </ShowcaseItem>
                    <ShowcaseItem component="KeyValueCard">
                        <dl className="meta">
                            <KeyValueCard
                                label={t("showCase.labels.userId")}
                                value={user?.id ?? "-"}
                            />
                            <KeyValueCard
                                label={t("showCase.labels.name")}
                                value={user?.name ?? "-"}
                            />
                            <KeyValueCard
                                label={t("showCase.labels.email")}
                                value={user?.email ?? "-"}
                            />
                        </dl>
                    </ShowcaseItem>
                    <ShowcaseItem component="InfoCard">
                        <InfoCard title="Info" message="Information status card example." />
                    </ShowcaseItem>
                    <ShowcaseItem component="WarningCard">
                        <WarningCard title="Warning" message="Warning status card example." />
                    </ShowcaseItem>
                    <ShowcaseItem component="ErrorCard">
                        <ErrorCard title="Error" message="Error status card example." />
                    </ShowcaseItem>
                    <ShowcaseItem component="ValidationCard">
                        <ValidationCard
                            title="Validation sample"
                            rules={[
                                { isValid: true, label: "Contains uppercase" },
                                { isValid: true, label: "Contains number" },
                                { isValid: false, label: "Contains special character" },
                            ]}
                        />
                    </ShowcaseItem>
                    <ShowcaseItem component="OAuthOptionsCard">
                        <OAuthOptionsCard title="Option Card">
                            <div className="showcase-catalog__stack">
                                <Button type="button">Option item 1</Button>
                                <Button type="button">Option item 2</Button>
                            </div>
                        </OAuthOptionsCard>
                    </ShowcaseItem>
                </div>
            </section>
        </section>
    );
}
