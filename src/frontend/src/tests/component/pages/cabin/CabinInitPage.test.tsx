import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CabinInitPage } from "../../../../pages/cabin/CabinInitPage";
import type { GameState } from "../../../../hooks/api/game/useGameApi";
import i18n from "../../../../i18n";
import { renderWithRouter } from "../../../utils/renderWithRouter";

const getGameStateMock = vi.fn();
const syncRewardPackagesMock = vi.fn();
const claimRewardPackageMock = vi.fn();
const createCabinPlacementMock = vi.fn();
const deleteCabinPlacementMock = vi.fn();
const extractGameErrorDetailMock = vi.fn();
const resolveGameErrorMessageMock = vi.fn();
const logoutMock = vi.fn();
const navigateMock = vi.fn();

vi.mock("../../../../hooks/useAuth", () => ({
    useAuthContext: () => ({
        user: {
            id: 1,
            email: "octo@example.com",
            name: "Octo Dev",
            role: "user",
            profile_image_url: null,
            oauth_providers: ["github"],
            is_verified: true,
            created_at: "2026-09-03T00:00:00Z",
        },
        logout: logoutMock,
    }),
}));

vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
    return {
        ...actual,
        useNavigate: () => navigateMock,
    };
});

vi.mock("../../../../hooks/api/game/useGameApi", () => ({
    useGameApi: () => ({
        getGameState: getGameStateMock,
        syncRewardPackages: syncRewardPackagesMock,
        claimRewardPackage: claimRewardPackageMock,
        createCabinPlacement: createCabinPlacementMock,
        deleteCabinPlacement: deleteCabinPlacementMock,
        extractGameErrorDetail: extractGameErrorDetailMock,
        resolveGameErrorMessage: resolveGameErrorMessageMock,
    }),
}));

const gameState: GameState = {
    settings: {
        timezone: "Asia/Seoul",
        daily_cutoff_hour: 5,
        updated_at: "2026-09-03T00:00:00Z",
    },
    today: {
        reward_date: "2026-09-03",
        timezone: "Asia/Seoul",
        daily_cutoff_hour: 5,
        window_start: "2026-09-02T20:00:00Z",
        window_end: "2026-09-03T20:00:00Z",
        total_activity_count: 8,
        total_points: 40,
        raw_coins: 24,
        coins: 24,
        food: 3,
        pet_exp: 160,
        items: [],
    },
    wallet: {
        coins: 120,
        updated_at: "2026-09-03T00:00:00Z",
    },
    inventory: [
        {
            item_type: "FOOD",
            item_key: "basic_feed",
            quantity: 3,
            metadata: {},
            updated_at: "2026-09-03T00:00:00Z",
        },
    ],
    categorized_inventory: {
        supplies: [
            {
                item_type: "FOOD",
                item_key: "basic_feed",
                quantity: 3,
                metadata: {},
                updated_at: "2026-09-03T00:00:00Z",
            },
        ],
        furniture: [
            {
                reward_key: "stack.terminal-desk",
                reward_type: "FURNITURE",
                source_language: "TypeScript",
                stack_reward_level: 1,
                stage: 1,
                exp: 0,
                is_featured: false,
                updated_at: "2026-09-03T00:00:00Z",
            },
        ],
        pet_logs: [
            {
                reward_key: "default.octocat",
                reward_type: "ANIMAL",
                source_language: "GitHub",
                stack_reward_level: 1,
                stage: 1,
                exp: 0,
                is_featured: true,
                updated_at: "2026-09-03T00:00:00Z",
            },
            {
                reward_key: "stack.python-serpent",
                reward_type: "ANIMAL",
                source_language: "Python",
                stack_reward_level: 1,
                stage: 1,
                exp: 0,
                is_featured: false,
                updated_at: "2026-09-03T00:00:00Z",
            },
        ],
    },
    collection: {
        furniture: [
            {
                reward_key: "stack.terminal-desk",
                reward_type: "FURNITURE",
                source_language: "TypeScript",
                asset_key: "typescript-terminal-desk",
                owned: true,
                required_mastery_level: 1,
                required_bytes: 50000,
                required_recent_activity_count: 10,
                condition_key: "stack_bytes",
                stack_reward_level: 1,
                stage: 1,
                mastery_level: 2,
                total_bytes: 443000,
                repository_count: 4,
            },
            {
                reward_key: "stack.forge-bench",
                reward_type: "FURNITURE",
                source_language: "Rust",
                asset_key: "rust-forge-bench",
                owned: false,
                required_mastery_level: 1,
                required_bytes: 50000,
                required_recent_activity_count: 10,
                condition_key: "stack_bytes",
                stack_reward_level: 0,
                stage: 0,
                mastery_level: 0,
                total_bytes: 0,
                repository_count: 0,
            },
            {
                reward_key: "event.night-owl-bed",
                reward_type: "FURNITURE",
                source_language: "Achievement",
                asset_key: "event-night-owl-bed",
                owned: false,
                required_mastery_level: 1,
                required_bytes: 50000,
                required_recent_activity_count: 10,
                condition_key: "night_owl_commits",
                stack_reward_level: 0,
                stage: 0,
                mastery_level: 0,
                total_bytes: 0,
                repository_count: 0,
            },
        ],
        pet_logs: [
            {
                reward_key: "default.octocat",
                reward_type: "ANIMAL",
                source_language: "GitHub",
                asset_key: "default-octocat",
                owned: true,
                required_mastery_level: 0,
                required_bytes: 0,
                required_recent_activity_count: 0,
                condition_key: "github_account",
                stack_reward_level: 1,
                stage: 1,
                mastery_level: 0,
                total_bytes: 0,
                repository_count: 0,
            },
            {
                reward_key: "stack.python-serpent",
                reward_type: "ANIMAL",
                source_language: "Python",
                asset_key: "python-serpent",
                owned: true,
                required_mastery_level: 1,
                required_bytes: 50000,
                required_recent_activity_count: 10,
                condition_key: "stack_bytes",
                stack_reward_level: 1,
                stage: 1,
                mastery_level: 1,
                total_bytes: 150000,
                repository_count: 2,
            },
            {
                reward_key: "stack.night-fox",
                reward_type: "ANIMAL",
                source_language: "Kotlin",
                asset_key: "kotlin-night-fox",
                owned: false,
                required_mastery_level: 1,
                required_bytes: 50000,
                required_recent_activity_count: 10,
                condition_key: "stack_bytes",
                stack_reward_level: 0,
                stage: 0,
                mastery_level: 0,
                total_bytes: 0,
                repository_count: 0,
            },
            {
                reward_key: "event.streak-spark",
                reward_type: "ANIMAL",
                source_language: "Achievement",
                asset_key: "event-streak-spark",
                owned: false,
                required_mastery_level: 1,
                required_bytes: 50000,
                required_recent_activity_count: 10,
                condition_key: "activity_streak",
                stack_reward_level: 0,
                stage: 0,
                mastery_level: 0,
                total_bytes: 0,
                repository_count: 0,
            },
        ],
    },
    cabin: {
        id: 1,
        width: 12,
        depth: 12,
        tile_width: 60,
        tile_height: 30,
        tile_z_height: 46,
        placements: [
            {
                id: 17,
                object_type: "FURNITURE",
                object_key: "stack.terminal-desk",
                x: 5,
                y: 5,
                z: 0,
                rotation: 0,
                width: 1,
                depth: 1,
                locked: false,
                updated_at: "2026-09-03T00:00:00Z",
            },
        ],
        updated_at: "2026-09-03T00:00:00Z",
    },
    stack_profiles: {
        items: [
            {
                language: "TypeScript",
                total_bytes: 443000,
                ratio: 0.58,
                repository_count: 4,
                recent_activity_count: 8,
                active_days_30d: 3,
                score: 87.5,
                tier: 2,
                mastery_level: 2,
                calculated_at: "2026-09-03T00:00:00Z",
            },
        ],
    },
    stack_rewards: [
        {
            reward_key: "stack.terminal-desk",
            reward_type: "FURNITURE",
            source_language: "TypeScript",
            stack_reward_level: 1,
            stage: 1,
            exp: 0,
            is_featured: false,
            updated_at: "2026-09-03T00:00:00Z",
        },
    ],
    pending_packages: [
        {
            id: 9,
            source: "GITHUB_SYNC",
            status: "PENDING",
            title: "TypeScript origin package",
            description: "TypeScript stack reward is ready.",
            created_at: "2026-09-03T00:00:00Z",
            metadata: {
                language: "TypeScript",
                mastery_level: 1,
                reward_key: "stack.terminal-desk",
                reward_type: "FURNITURE",
            },
            items: [
                {
                    id: 11,
                    item_type: "STACK_REWARD_UPGRADE",
                    item_key: "stack.terminal-desk",
                    quantity: 1,
                    metadata: {},
                },
            ],
        },
    ],
};

describe("CabinInitPage", () => {
    beforeEach(() => {
        getGameStateMock.mockReset();
        syncRewardPackagesMock.mockReset();
        claimRewardPackageMock.mockReset();
        deleteCabinPlacementMock.mockReset();
        createCabinPlacementMock.mockReset();
        extractGameErrorDetailMock.mockReset();
        resolveGameErrorMessageMock.mockReset();
        logoutMock.mockReset();
        navigateMock.mockReset();
        logoutMock.mockResolvedValue(undefined);
        void i18n.changeLanguage("en");
        window.localStorage.clear();
        getGameStateMock.mockResolvedValue(gameState);
        syncRewardPackagesMock.mockResolvedValue([]);
        deleteCabinPlacementMock.mockResolvedValue(undefined);
        createCabinPlacementMock.mockResolvedValue({
            id: 18,
            object_type: "STACK_REWARD",
            object_key: "default.octocat",
            x: 6,
            y: 6,
            z: 0,
            rotation: 0,
            width: 1,
            depth: 1,
            locked: false,
            updated_at: "2026-09-03T00:00:00Z",
        });
        claimRewardPackageMock.mockResolvedValue({
            package: { ...gameState.pending_packages?.[0], status: "CLAIMED" },
            stack_rewards: gameState.categorized_inventory.furniture,
            wallet: gameState.wallet,
            inventory: gameState.categorized_inventory.supplies,
        });
        extractGameErrorDetailMock.mockReturnValue(null);
        resolveGameErrorMessageMock.mockReturnValue("Could not load cabin state.");
    });

    it("loads the playable init state and opens package details", async () => {
        // Given: backend game state is available for the current user.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");

        // Then: the init board shows player and summary data from the backend state.
        expect(await screen.findByText("Octo Dev")).toBeVisible();
        expect(screen.getByTestId("cabin-phaser-stage")).toBeInTheDocument();
        expect(screen.getByText("120")).toBeVisible();
        expect(screen.getByText("8")).toBeVisible();
        expect(screen.getByText("3")).toBeVisible();

        // When: the user opens packages.
        await user.click(screen.getByRole("button", { name: "Packages" }));

        // Then: the transparent package modal shows pending reward data.
        const dialog = screen.getByRole("dialog", { name: "Packages" });
        expect(within(dialog).getByText("TypeScript origin package")).toBeVisible();
        expect(within(dialog).getByText("TypeScript stack reward is ready.")).toBeVisible();
    });

    it("claims a package and refreshes the cabin state", async () => {
        // Given: a pending reward package is visible.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        expect(await screen.findByText("Octo Dev")).toBeVisible();
        await user.click(screen.getByRole("button", { name: "Packages" }));

        // When: the player claims the package.
        await user.click(screen.getByRole("button", { name: "Claim" }));

        // Then: the backend claim route is called and the cabin state is reloaded.
        await waitFor(() => expect(claimRewardPackageMock).toHaveBeenCalledWith(9));
        expect(getGameStateMock).toHaveBeenCalledTimes(3);
    });

    it("groups claimed rewards by inventory category", async () => {
        // Given: the cabin state includes supplies, furniture, and pet logs.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        expect(await screen.findByText("Octo Dev")).toBeVisible();

        // When: the player opens inventory.
        await user.click(screen.getByRole("button", { name: "Inventory" }));

        // Then: claimed items are separated into all three inventory groups.
        const dialog = screen.getByRole("dialog", { name: "Inventory" });
        expect(within(dialog).getByRole("tab", { name: "Supplies" })).toBeVisible();
        expect(within(dialog).getByText("Basic feed")).toBeVisible();
        expect(within(dialog).getByText("Owned quantity: 3.")).toBeVisible();
        await user.click(within(dialog).getByRole("tab", { name: "Furniture" }));
        expect(within(dialog).getByText("TypeScript terminal desk")).toBeVisible();
        expect(within(dialog).getByText("Placed in the cabin.")).toBeVisible();
        await user.click(within(dialog).getByRole("tab", { name: "Pet logs" }));
        expect(
            within(dialog).getByRole("button", { name: "Python serpent pet log" }),
        ).toBeVisible();
    });

    it("collects a placed inventory reward from the cabin", async () => {
        // Given: a claimed furniture reward is already placed in the cabin.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        expect(await screen.findByText("Octo Dev")).toBeVisible();

        // When: the player opens inventory and collects the placed furniture.
        await user.click(screen.getByRole("button", { name: "Inventory" }));
        const dialog = screen.getByRole("dialog", { name: "Inventory" });
        await user.click(within(dialog).getByRole("tab", { name: "Furniture" }));
        await user.click(within(dialog).getByRole("button", { name: "Collect" }));

        // Then: the cabin placement delete API is used without reloading the full cabin state.
        await waitFor(() => expect(deleteCabinPlacementMock).toHaveBeenCalledWith(17));
        expect(getGameStateMock).toHaveBeenCalledTimes(2);
    });

    it("starts manual placement for the default Octocat pet log from inventory", async () => {
        // Given: the GitHub default pet log is owned but not placed.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        expect(await screen.findByText("Octo Dev")).toBeVisible();

        // When: the player opens pet logs and places the Octocat.
        await user.click(screen.getByRole("button", { name: "Inventory" }));
        const dialog = screen.getByRole("dialog", { name: "Inventory" });
        await user.click(within(dialog).getByRole("tab", { name: "Pet logs" }));
        expect(within(dialog).getByText("Cabin Log Octocat pet log")).toBeVisible();
        await user.click(within(dialog).getByRole("button", { name: "Place" }));

        // Then: placement waits for a Phaser grid click instead of reloading immediately.
        expect(screen.queryByRole("dialog", { name: "Inventory" })).not.toBeInTheDocument();
        expect(screen.getByTestId("cabin-phaser-stage")).toHaveClass("cabin-phaser-stage--placing");
        expect(createCabinPlacementMock).not.toHaveBeenCalled();
        expect(getGameStateMock).toHaveBeenCalledTimes(2);
    });

    it("tracks furniture and pet logs in the collection", async () => {
        // Given: supplies and stack rewards have been claimed.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        expect(await screen.findByText("Octo Dev")).toBeVisible();

        // When: the player opens the collection.
        await user.click(screen.getByRole("button", { name: "Collection" }));

        // Then: owned entries show names, while locked entries reveal details only when selected.
        const dialog = screen.getByRole("dialog", { name: "Collection" });
        expect(within(dialog).getAllByText("TypeScript terminal desk")[0]).toBeVisible();
        expect(within(dialog).queryByText("Rust forge bench")).not.toBeInTheDocument();
        await user.click(within(dialog).getByRole("button", { name: /\?RustLocked/ }));
        expect(within(dialog).getByText("Rust forge bench")).toBeVisible();
        expect(
            within(dialog).getByText(
                "Unlock by syncing Rust work with at least 50,000 bytes, or 10 recent Rust activities.",
            ),
        ).toBeVisible();
        await user.click(within(dialog).getByRole("button", { name: /\?AchievementLocked/ }));
        expect(within(dialog).getByText("Night owl bed")).toBeVisible();
        expect(
            within(dialog).getByText(
                "Unlock by making 10 commits between midnight and 05:00 in your timezone.",
            ),
        ).toBeVisible();
        await user.click(within(dialog).getByRole("tab", { name: "Pet logs" }));
        expect(
            within(dialog).getByRole("button", { name: "Python serpent pet logPythonOwned" }),
        ).toBeVisible();
        await user.click(within(dialog).getByRole("button", { name: /\?KotlinLocked/ }));
        expect(within(dialog).getByText("Kotlin night fox pet log")).toBeVisible();
        await user.click(within(dialog).getByRole("button", { name: /\?AchievementLocked/ }));
        expect(within(dialog).getByText("Activity streak spark pet log")).toBeVisible();
        expect(within(dialog).queryByText("Basic feed")).not.toBeInTheDocument();
    });

    it("runs the automatic daily reward refresh once per reward date", async () => {
        // Given: the player opens the cabin for the first time on the reward date.
        const { unmount } = renderWithRouter(<CabinInitPage />, "/cabin");

        // Then: the page creates the daily reward package and reloads game state once.
        expect(await screen.findByText("Octo Dev")).toBeVisible();
        await waitFor(() => expect(syncRewardPackagesMock).toHaveBeenCalledTimes(1));
        expect(syncRewardPackagesMock).toHaveBeenCalledWith();
        expect(getGameStateMock).toHaveBeenCalledTimes(2);

        // When: the page is opened again on the same reward date.
        unmount();
        getGameStateMock.mockClear();
        syncRewardPackagesMock.mockClear();
        renderWithRouter(<CabinInitPage />, "/cabin");

        // Then: the automatic refresh is skipped because the daily attempt already completed.
        expect(await screen.findByText("Octo Dev")).toBeVisible();
        await waitFor(() => expect(getGameStateMock).toHaveBeenCalledTimes(1));
        expect(syncRewardPackagesMock).not.toHaveBeenCalled();
    });

    it("updates daily rewards when the player clicks refresh", async () => {
        // Given: the cabin state is visible after the automatic refresh.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        expect(await screen.findByText("Octo Dev")).toBeVisible();
        await waitFor(() => expect(syncRewardPackagesMock).toHaveBeenCalledTimes(1));

        // When: the player manually refreshes daily rewards.
        await user.click(screen.getByRole("button", { name: "Update daily rewards" }));

        // Then: the page asks the backend to refresh rewards again and reloads state.
        await waitFor(() => expect(syncRewardPackagesMock).toHaveBeenCalledTimes(2));
        expect(syncRewardPackagesMock).toHaveBeenLastCalledWith();
        expect(getGameStateMock).toHaveBeenCalledTimes(3);
    });

    it("localizes package names from package metadata", async () => {
        // Given: the player uses Korean while package titles are stored in English.
        const user = userEvent.setup();
        await i18n.changeLanguage("ko");
        renderWithRouter(<CabinInitPage />, "/cabin");
        expect(await screen.findByText("Octo Dev")).toBeVisible();

        // When: the user opens packages.
        await user.click(screen.getByRole("button", { name: "소포" }));

        // Then: the modal renders a localized title from package metadata.
        const dialog = screen.getByRole("dialog", { name: "소포" });
        expect(within(dialog).getByText("TypeScript 시작 소포")).toBeVisible();
        expect(within(dialog).getByText("TypeScript 스택 보상이 준비되었습니다.")).toBeVisible();
        expect(within(dialog).getByText("1개 아이템")).toBeVisible();
    });

    it("localizes achievement package names from package metadata", async () => {
        // Given: an event reward package arrived from achievement sync.
        const user = userEvent.setup();
        await i18n.changeLanguage("ko");
        getGameStateMock.mockResolvedValue({
            ...gameState,
            pending_packages: [
                {
                    id: 12,
                    source: "ACHIEVEMENT",
                    status: "PENDING",
                    title: "event.night-owl-bed achievement package",
                    description: "event.night-owl-bed event reward is ready.",
                    created_at: "2026-09-03T00:00:00Z",
                    metadata: {
                        grant_type: "event_reward",
                        condition_key: "night_owl_commits",
                        reward_key: "event.night-owl-bed",
                        reward_type: "FURNITURE",
                    },
                    items: [
                        {
                            id: 12,
                            item_type: "STACK_REWARD_UPGRADE",
                            item_key: "event.night-owl-bed",
                            quantity: 1,
                            metadata: {},
                        },
                    ],
                },
            ],
        });
        renderWithRouter(<CabinInitPage />, "/cabin");
        expect(await screen.findByText("Octo Dev")).toBeVisible();

        // When: the user opens packages.
        await user.click(screen.getByRole("button", { name: "소포" }));

        // Then: the package uses the localized reward name instead of the raw reward key.
        const dialog = screen.getByRole("dialog", { name: "소포" });
        expect(within(dialog).getByText("새벽 작업 침대 업적 소포")).toBeVisible();
        expect(
            within(dialog).getByText("활동 업적을 달성해 새벽 작업 침대 보상이 준비되었습니다."),
        ).toBeVisible();
    });

    it("reveals the cabin scene when reached from the login success callback", async () => {
        // Given: login success redirected the user to the cabin with entry reveal state.
        const { container } = render(
            <MemoryRouter
                initialEntries={[
                    {
                        pathname: "/cabin",
                        state: { playCabinEntryReveal: true },
                    },
                ]}
            >
                <CabinInitPage />
            </MemoryRouter>,
        );

        // Then: the cabin screen loads normally while applying the reveal animation class.
        expect(await screen.findByText("Octo Dev")).toBeVisible();
        expect(container.querySelector(".cabin-init-page")).toHaveClass(
            "cabin-init-page--entry-reveal",
        );
    });

    it("opens backend-backed settings details", async () => {
        // Given: backend game state includes settings and cabin dimensions.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        await screen.findByText("Octo Dev");

        // When: the user opens settings.
        await user.click(screen.getByRole("button", { name: "Settings" }));

        // Then: settings are shown without navigating away from the playable init screen.
        const dialog = screen.getByRole("dialog", { name: "Cabin settings" });
        expect(within(dialog).getByText("Asia/Seoul")).toBeVisible();
        expect(within(dialog).getByText("12 x 12 cells, 60 x 30 px tiles")).toBeVisible();
        expect(within(dialog).getByText("TypeScript")).toBeVisible();
        expect(within(dialog).getByText("GitHub profile connected")).toBeVisible();
        expect(within(dialog).getByText("octo@example.com")).toBeVisible();
    });

    it("changes the cabin settings language in place", async () => {
        // Given: the settings modal is open in English.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        await screen.findByText("Octo Dev");
        await user.click(screen.getByRole("button", { name: "Settings" }));
        expect(screen.getByRole("dialog", { name: "Cabin settings" })).toBeVisible();

        // When: the user switches to Korean.
        await user.click(screen.getByRole("button", { name: "한국어" }));

        // Then: the modal updates without leaving the cabin page.
        expect(await screen.findByRole("dialog", { name: "오두막 설정" })).toBeVisible();
        expect(screen.getByRole("button", { name: "로그아웃" })).toBeVisible();
    });

    it("logs out from the settings modal and returns to login", async () => {
        // Given: the authenticated user is viewing cabin settings.
        const user = userEvent.setup();
        renderWithRouter(<CabinInitPage />, "/cabin");
        await screen.findByText("Octo Dev");
        await user.click(screen.getByRole("button", { name: "Settings" }));

        // When: the user signs out from the settings modal.
        await user.click(screen.getByRole("button", { name: "Sign out" }));

        // Then: the auth session is cleared and the user returns to login.
        expect(logoutMock).toHaveBeenCalledTimes(1);
        expect(navigateMock).toHaveBeenCalledWith("/login", { replace: true });
    });
});
