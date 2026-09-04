import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";

const reloadConfigMock = vi.fn();
const useAppConfigMock = vi.fn();
const checkNowMock = vi.fn();

vi.mock("../../hooks/useFeatures", () => ({
    useAppConfig: () => useAppConfigMock(),
}));

vi.mock("../../hooks/connectivity/useServerConnectivity", () => ({
    useServerConnectivity: () => ({
        isDesktop: true,
        status: "offline",
        checkNow: checkNowMock,
    }),
}));

describe("App configuration guard", () => {
    beforeEach(() => {
        reloadConfigMock.mockReset();
        checkNowMock.mockReset();
        checkNowMock.mockResolvedValue(undefined);
        reloadConfigMock.mockRejectedValue(new Error("server unavailable"));
        useAppConfigMock.mockReturnValue({
            data: null,
            loading: false,
            error: new Error("config unavailable"),
            reload: reloadConfigMock,
        });
    });

    it("keeps protected routes locked when server configuration is unavailable", async () => {
        // Given: desktop startup cannot load /config and the requested URL is protected.
        render(
            <MemoryRouter initialEntries={["/cabin"]}>
                <App />
            </MemoryRouter>,
        );

        // Then: the app fails closed instead of treating login as disabled or showing a fake user.
        expect(screen.getByRole("heading", { name: "Server unavailable" })).toBeInTheDocument();
        expect(screen.getByText(/protected pages remain locked/i)).toBeInTheDocument();
        expect(screen.queryByText("User")).not.toBeInTheDocument();
        const publicNav = screen.getByRole("banner", {
            name: "Server connection navigation",
        });
        expect(within(publicNav).getByText("Cabinlog")).toBeInTheDocument();
        expect(within(publicNav).getByRole("status")).toBeInTheDocument();

        // When: the user requests another connection attempt.
        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: "Retry connection" }));

        // Then: the application configuration is requested again.
        expect(reloadConfigMock).toHaveBeenCalledTimes(1);
    });

    it("does not flash the retry loading indicator for immediate retry clicks", async () => {
        // Given: a manual retry remains in flight.
        reloadConfigMock.mockReturnValue(new Promise(() => undefined));
        render(
            <MemoryRouter initialEntries={["/cabin"]}>
                <App />
            </MemoryRouter>,
        );

        // When: the user requests another connection attempt.
        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: "Retry connection" }));

        // Then: the button is locked, but the short retry state does not flash a loading label.
        expect(screen.getByRole("button", { name: "Retry connection" })).toBeDisabled();
        expect(screen.queryByText("Retrying connection...")).not.toBeInTheDocument();
    });
});
