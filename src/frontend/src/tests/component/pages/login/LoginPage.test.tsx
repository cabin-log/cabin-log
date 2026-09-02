import { fireEvent, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "../../../../pages/login/LoginPage";
import { renderWithRouter } from "../../../utils/renderWithRouter";

const getOAuthProvidersMock = vi.fn();
const useAppConfigMock = vi.fn();

vi.mock("../../../../hooks/useFeatures", () => ({
    useAppConfig: () => useAppConfigMock(),
}));

vi.mock("../../../../hooks/api/auth/useAuthApi", () => ({
    useAuthApi: () => ({
        getOAuthProviders: getOAuthProvidersMock,
    }),
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
