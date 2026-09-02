import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppNavbar } from "../../../../components/layout/AppNavbar";
import { renderWithRouter } from "../../../utils/renderWithRouter";

const checkNowMock = vi.fn();
const logoutMock = vi.fn();
let connectivityStatus = "offline";

vi.mock("../../../../hooks/useAuth", () => ({
    useAuthContext: () => ({
        user: { email: "user@example.com", name: "User" },
        logout: logoutMock,
    }),
}));

vi.mock("../../../../hooks/useFeatures", () => ({
    useAppConfig: () => ({ data: { login_enabled: true } }),
}));

vi.mock("../../../../hooks/connectivity/useServerConnectivity", () => ({
    useServerConnectivity: () => ({
        isDesktop: true,
        status: connectivityStatus,
        checkNow: checkNowMock,
    }),
}));

describe("AppNavbar", () => {
    beforeEach(() => {
        connectivityStatus = "offline";
        checkNowMock.mockReset();
        checkNowMock.mockResolvedValue(undefined);
        logoutMock.mockReset();
        logoutMock.mockResolvedValue(undefined);
    });

    it("places disconnected status beside the profile control", () => {
        // Given/When: an authenticated desktop screen loses server connectivity.
        const { container } = renderWithRouter(<AppNavbar />, "/settings");

        // Then: the compact status and profile control share the navbar action group.
        const actions = container.querySelector(".app-nav__actions");
        expect(actions).toContainElement(screen.getByRole("status"));
        expect(actions).toContainElement(screen.getByRole("button", { name: "Open profile menu" }));
    });

    it("keeps the disconnected label stable during a manual retry", async () => {
        // Given: the server is disconnected and the manual retry takes time.
        let resolveRetry: () => void = () => undefined;
        checkNowMock.mockReturnValue(
            new Promise<void>((resolve) => {
                resolveRetry = resolve;
            }),
        );
        const user = userEvent.setup();
        renderWithRouter(<AppNavbar />, "/settings");

        // When: the user clicks the navbar status button.
        const retryButton = screen.getByRole("button", { name: "Retry now" });
        await user.click(retryButton);

        // Then: the compact pill stays visually anchored instead of flashing to a reconnecting state.
        expect(retryButton).toHaveTextContent("Server disconnected");
        expect(screen.queryByText("Reconnecting")).not.toBeInTheDocument();
        expect(retryButton).toBeDisabled();

        resolveRetry();
        await waitFor(() => expect(retryButton).not.toBeDisabled());
    });

    it("blocks logout while the desktop server is disconnected", async () => {
        // Given: an authenticated desktop user is offline on the main page.
        const user = userEvent.setup();
        renderWithRouter(<AppNavbar />, "/show-case");

        // When: the user opens the profile menu.
        await user.click(screen.getByRole("button", { name: "Open profile menu" }));

        // Then: logout is unavailable instead of clearing local session and routing to login.
        const logoutButton = screen.getByRole("menuitem", { name: "Sign out" });
        expect(logoutButton).toBeDisabled();
        await user.click(logoutButton);
        expect(logoutMock).not.toHaveBeenCalled();
    });
});
