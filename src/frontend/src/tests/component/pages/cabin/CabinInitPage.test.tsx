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
    inventory: [],
    cabin: {
        id: 1,
        width: 12,
        depth: 12,
        tile_width: 60,
        tile_height: 30,
        tile_z_height: 46,
        placements: [],
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
    stack_rewards: [],
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
        extractGameErrorDetailMock.mockReset();
        resolveGameErrorMessageMock.mockReset();
        logoutMock.mockReset();
        navigateMock.mockReset();
        logoutMock.mockResolvedValue(undefined);
        void i18n.changeLanguage("en");
        window.localStorage.clear();
        getGameStateMock.mockResolvedValue(gameState);
        syncRewardPackagesMock.mockResolvedValue([]);
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
