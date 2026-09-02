import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DesktopTitleBar } from "../../../../components/layout/DesktopTitleBar";
import { renderWithRouter } from "../../../utils/renderWithRouter";

const minimizeMock = vi.fn().mockResolvedValue(undefined);
const toggleMaximizeMock = vi.fn().mockResolvedValue(undefined);
const closeMock = vi.fn().mockResolvedValue(undefined);
const startDraggingMock = vi.fn().mockResolvedValue(undefined);
const checkNowMock = vi.fn().mockResolvedValue(undefined);

vi.mock("@tauri-apps/api/window", () => ({
    getCurrentWindow: () => ({
        minimize: minimizeMock,
        toggleMaximize: toggleMaximizeMock,
        close: closeMock,
        startDragging: startDraggingMock,
    }),
}));

vi.mock("../../../../hooks/connectivity/useServerConnectivity", () => ({
    useServerConnectivity: () => ({
        isDesktop: true,
        status: "offline",
        checkNow: checkNowMock,
    }),
}));

function setTauriUserAgent(userAgent: string) {
    Object.defineProperty(window, "__TAURI_INTERNALS__", {
        configurable: true,
        value: {},
    });
    Object.defineProperty(window.navigator, "userAgent", {
        configurable: true,
        value: userAgent,
    });
}

afterEach(() => {
    Reflect.deleteProperty(window, "__TAURI_INTERNALS__");
    minimizeMock.mockClear();
    toggleMaximizeMock.mockClear();
    closeMock.mockClear();
    startDraggingMock.mockClear();
    checkNowMock.mockClear();
});

describe("DesktopTitleBar", () => {
    it("stays hidden in the browser frontend", () => {
        renderWithRouter(<DesktopTitleBar />, "/login");

        expect(screen.queryByRole("button", { name: "Minimize window" })).not.toBeInTheDocument();
    });

    it("connects custom Windows controls to Tauri window actions", async () => {
        setTauriUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64)");
        renderWithRouter(<DesktopTitleBar />, "/login");
        const user = userEvent.setup();

        await user.click(screen.getByRole("button", { name: "Minimize window" }));
        await user.click(screen.getByRole("button", { name: "Maximize or restore window" }));
        await user.click(screen.getByRole("button", { name: "Close window" }));

        expect(minimizeMock).toHaveBeenCalledTimes(1);
        expect(toggleMaximizeMock).toHaveBeenCalledTimes(1);
        expect(closeMock).toHaveBeenCalledTimes(1);
    });

    it("uses native window controls on macOS", () => {
        setTauriUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)");
        const { container } = renderWithRouter(<DesktopTitleBar />, "/login");

        expect(container.querySelector(".desktop-titlebar--standalone")).toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Close window" })).not.toBeInTheDocument();
    });

    it("places disconnected status in standalone titlebar tools", () => {
        setTauriUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)");
        const { container } = renderWithRouter(<DesktopTitleBar />, "/login");

        const tools = container.querySelector(".desktop-titlebar__tools");
        expect(tools).toContainElement(screen.getByRole("status"));
    });

    it("starts native dragging from a standalone navbar surface", () => {
        setTauriUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)");
        const { container } = renderWithRouter(<DesktopTitleBar />, "/login");

        fireEvent.mouseDown(container.querySelector(".desktop-titlebar--standalone")!, {
            button: 0,
        });

        expect(startDraggingMock).toHaveBeenCalledTimes(1);
    });

    it("does not drag when a titlebar control is pressed", () => {
        setTauriUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)");
        renderWithRouter(<DesktopTitleBar />, "/login");

        fireEvent.mouseDown(screen.getByRole("button", { name: "Retry now" }), { button: 0 });

        expect(startDraggingMock).not.toHaveBeenCalled();
    });

    it("retries connectivity without starting a window drag", async () => {
        setTauriUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)");
        renderWithRouter(<DesktopTitleBar />, "/login");
        const retryButton = screen.getByRole("button", { name: "Retry now" });

        fireEvent.mouseDown(retryButton, { button: 0 });
        await userEvent.setup().click(retryButton);

        expect(startDraggingMock).not.toHaveBeenCalled();
        expect(checkNowMock).toHaveBeenCalledTimes(1);
    });

    it("keeps standalone tools out of an integrated app navbar", () => {
        setTauriUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)");
        const { container } = renderWithRouter(<DesktopTitleBar />, "/settings");

        expect(container.querySelector(".desktop-titlebar__tools")).not.toBeInTheDocument();
    });
});
