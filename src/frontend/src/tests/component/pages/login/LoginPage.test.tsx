import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "../../../../pages/login/LoginPage";
import { renderWithRouter } from "../../../utils/renderWithRouter";

const getOAuthProvidersMock = vi.fn();
const useAppConfigMock = vi.fn();
const useAuthContextMock = vi.fn();

vi.mock("../../../../hooks/useFeatures", () => ({
    useAppConfig: () => useAppConfigMock(),
}));

vi.mock("../../../../hooks/api/auth/useAuthApi", () => ({
    useAuthApi: () => ({
        getOAuthProviders: getOAuthProvidersMock,
    }),
}));

vi.mock("../../../../hooks/useAuth", () => ({
    useAuthContext: () => useAuthContextMock(),
}));

describe("LoginPage", () => {
    beforeEach(() => {
        getOAuthProvidersMock.mockReset();
        useAppConfigMock.mockReturnValue({
            data: {
                login_enabled: true,
                email_enabled: false,
                oauth_enabled: true,
            },
            loading: false,
        });
        useAuthContextMock.mockReturnValue({
            user: null,
            loading: false,
        });
    });

    it("shows only GitHub OAuth login when GitHub provider is enabled", async () => {
        // Given: the backend exposes GitHub as an OAuth provider.
        getOAuthProvidersMock.mockResolvedValue({
            providers: [
                { provider: "github", start_path: "/api/v1/auth/oauth/github/start" },
                { provider: "google", start_path: "/api/v1/auth/oauth/google/start" },
            ],
        });

        // When: login page is rendered.
        renderWithRouter(<LoginPage />, "/login");

        // Then: only the GitHub login action is available.
        expect(screen.getByRole("img", { name: "Cabin Log" })).toBeVisible();
        expect(
            screen.getByRole("link", { name: "Open Cabinlog GitHub repository" }),
        ).toHaveAttribute("href", "https://github.com/cabin-log/cabin-log");
        expect(await screen.findByRole("button", { name: "Continue with GitHub" })).toBeVisible();
        expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
        expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Sign in" })).not.toBeInTheDocument();
        expect(screen.queryByRole("link", { name: "Create an account" })).not.toBeInTheDocument();
        expect(screen.queryByRole("link", { name: "Find your password" })).not.toBeInTheDocument();
        expect(
            screen.queryByRole("button", { name: "Continue with Google" }),
        ).not.toBeInTheDocument();
    });

    it("shows a recent GitHub account shortcut and a GitHub re-login action", async () => {
        // Given: a previous GitHub login account was remembered in this browser.
        window.localStorage.setItem(
            "cabinlog:login:v1:recent-account",
            JSON.stringify({
                userId: 7,
                email: "octo@example.com",
                name: "Octo Dev",
                profileImageUrl: null,
                provider: "github",
                updatedAt: "2026-09-02T00:00:00.000Z",
            }),
        );
        getOAuthProvidersMock.mockResolvedValue({
            providers: [{ provider: "github", start_path: "/api/v1/auth/oauth/github/start" }],
        });

        // When: login page is rendered.
        renderWithRouter(<LoginPage />, "/login");

        // Then: the remembered account is available and the default OAuth button becomes re-login.
        expect(await screen.findByRole("button", { name: "Start as Octo Dev" })).toBeVisible();
        expect(screen.getByText("octo@example.com")).toBeVisible();
        expect(screen.getByRole("button", { name: "Sign in with GitHub again" })).toBeVisible();
    });

    it("starts the cabin entry sequence before GitHub OAuth navigation", async () => {
        // Given: GitHub login is ready.
        getOAuthProvidersMock.mockResolvedValue({
            providers: [{ provider: "github", start_path: "/api/v1/auth/oauth/github/start" }],
        });

        // When: the GitHub login action is clicked.
        const { container } = renderWithRouter(<LoginPage />, "/login");
        const githubLoginButton = await screen.findByRole("button", {
            name: "Continue with GitHub",
        });
        fireEvent.click(githubLoginButton);

        // Then: the page starts the cabin entry animation and prevents duplicate clicks.
        expect(container.querySelector(".auth-page")).toHaveClass("auth-page--entering-cabin");
        expect(githubLoginButton).toBeDisabled();
    });

    it("resets the cabin entry sequence when the login page is restored from browser history", async () => {
        // Given: a recent GitHub account is shown on the login page.
        window.localStorage.setItem(
            "cabinlog:login:v1:recent-account",
            JSON.stringify({
                userId: 7,
                email: "octo@example.com",
                name: "Octo Dev",
                profileImageUrl: null,
                provider: "github",
                updatedAt: "2026-09-02T00:00:00.000Z",
            }),
        );
        getOAuthProvidersMock.mockResolvedValue({
            providers: [{ provider: "github", start_path: "/api/v1/auth/oauth/github/start" }],
        });

        // When: entry starts and the page is restored from the browser back-forward cache.
        const { container } = renderWithRouter(<LoginPage />, "/login");
        const recentAccountButton = await screen.findByRole("button", {
            name: "Start as Octo Dev",
        });
        fireEvent.click(recentAccountButton);
        const pageshowEvent = new Event("pageshow") as PageTransitionEvent;
        Object.defineProperty(pageshowEvent, "persisted", { value: true });
        act(() => {
            window.dispatchEvent(pageshowEvent);
        });

        // Then: the animated entry state is cleared so the login page is usable again.
        await waitFor(() => {
            expect(container.querySelector(".auth-page")).not.toHaveClass(
                "auth-page--entering-cabin",
            );
        });
        expect(recentAccountButton).not.toBeDisabled();
    });

    it("shows an OAuth setup message when GitHub login is unavailable", async () => {
        // Given: OAuth is enabled but GitHub is not returned.
        getOAuthProvidersMock.mockResolvedValue({
            providers: [{ provider: "google", start_path: "/api/v1/auth/oauth/google/start" }],
        });

        // When: login page is rendered.
        renderWithRouter(<LoginPage />, "/login");

        // Then: the page explains that GitHub login needs server configuration.
        expect(
            await screen.findByText(
                "GitHub login is unavailable. Check the server OAuth settings.",
            ),
        ).toBeVisible();
        expect(
            screen.queryByRole("button", { name: "Continue with GitHub" }),
        ).not.toBeInTheDocument();
    });
});
