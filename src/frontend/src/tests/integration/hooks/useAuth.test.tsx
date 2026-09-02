import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuthContext } from "../../../hooks/useAuth";
import { FULL_SYSTEM_SCENARIO } from "../../fixtures/fullSystemScenarioData";

const getConfigMock = vi.fn();
const refreshMock = vi.fn();
const meMock = vi.fn();
const loginMock = vi.fn();
const signupMock = vi.fn();
const updateMeMock = vi.fn();
const logoutApiMock = vi.fn();

vi.mock("../../../hooks/api/config/useConfigApi", () => ({
    useConfigApi: () => ({
        getConfig: getConfigMock,
    }),
}));

vi.mock("../../../hooks/api/auth/useAuthApi", () => ({
    useAuthApi: () => ({
        refresh: refreshMock,
        me: meMock,
        login: loginMock,
        signup: signupMock,
        updateMe: updateMeMock,
        logout: logoutApiMock,
    }),
}));

function AuthProbe() {
    const { loading, user, logout } = useAuthContext();

    return (
        <section>
            <p data-testid="loading">{String(loading)}</p>
            <p data-testid="email">{user?.email ?? ""}</p>
            <button
                type="button"
                onClick={() => {
                    void logout().catch(() => undefined);
                }}
            >
                logout
            </button>
        </section>
    );
}

describe("useAuth bootstrap and exception flows", () => {
    beforeEach(() => {
        sessionStorage.clear();
        getConfigMock.mockReset();
        refreshMock.mockReset();
        meMock.mockReset();
        loginMock.mockReset();
        signupMock.mockReset();
        updateMeMock.mockReset();
        logoutApiMock.mockReset();
    });

    it("restores login from the session cookie after the tab-scoped token is lost", async () => {
        // Given: closing a tab removed its access token while the browser session cookie remains.
        getConfigMock.mockResolvedValue({ login_enabled: true });
        refreshMock.mockResolvedValue({ access_token: "refreshed-token" });
        meMock.mockResolvedValue(FULL_SYSTEM_SCENARIO.principal);

        // When: auth provider initializes.
        render(
            <AuthProvider>
                <AuthProbe />
            </AuthProvider>,
        );

        // Then: refresh-based bootstrap restores the user and a new tab-scoped access token.
        await waitFor(() => {
            expect(screen.getByTestId("loading").textContent).toBe("false");
        });
        expect(screen.getByTestId("email").textContent).toBe(FULL_SYSTEM_SCENARIO.principal.email);
        expect(sessionStorage.getItem("template_access_token")).toBe("refreshed-token");
        expect(refreshMock).toHaveBeenCalledTimes(1);
        expect(meMock).toHaveBeenCalledTimes(1);
    });

    it("keeps existing session when stored token allows /me success", async () => {
        // Given: existing token in storage and successful /me lookup.
        sessionStorage.setItem("template_access_token", "existing-token");
        getConfigMock.mockResolvedValue({ login_enabled: true });
        meMock.mockResolvedValue(FULL_SYSTEM_SCENARIO.principal);

        // When: auth provider initializes.
        render(
            <AuthProvider>
                <AuthProbe />
            </AuthProvider>,
        );

        // Then: provider uses existing token path without refresh call.
        await waitFor(() => {
            expect(screen.getByTestId("loading").textContent).toBe("false");
        });
        expect(screen.getByTestId("email").textContent).toBe(FULL_SYSTEM_SCENARIO.principal.email);
        expect(refreshMock).not.toHaveBeenCalled();
        expect(meMock).toHaveBeenCalledTimes(1);
        expect(sessionStorage.getItem("template_access_token")).toBe("existing-token");
    });

    it("remembers a GitHub account when session revalidation succeeds", async () => {
        // Given: an existing token resolves to a GitHub-connected user.
        sessionStorage.setItem("template_access_token", "existing-token");
        getConfigMock.mockResolvedValue({ login_enabled: true });
        meMock.mockResolvedValue({
            ...FULL_SYSTEM_SCENARIO.principal,
            id: 7,
            email: "octo@example.com",
            name: "Octo Dev",
            oauth_providers: ["github"],
        });

        // When: auth provider initializes.
        render(
            <AuthProvider>
                <AuthProbe />
            </AuthProvider>,
        );

        // Then: the session user is stored as the recent login account without storing tokens.
        await waitFor(() => {
            expect(screen.getByTestId("loading").textContent).toBe("false");
        });
        expect(window.localStorage.getItem("cabinlog:login:v1:recent-account")).toContain(
            "octo@example.com",
        );
    });

    it("clears session when /me fails and refresh also fails", async () => {
        // Given: existing token but both /me and refresh paths fail.
        sessionStorage.setItem("template_access_token", "stale-token");
        getConfigMock.mockResolvedValue({ login_enabled: true });
        meMock.mockRejectedValue(new Error("INVALID_TOKEN"));
        refreshMock.mockRejectedValue(new Error("INVALID_TOKEN"));

        // When: auth provider initializes.
        render(
            <AuthProvider>
                <AuthProbe />
            </AuthProvider>,
        );

        // Then: provider falls back to logged-out state and clears token.
        await waitFor(() => {
            expect(screen.getByTestId("loading").textContent).toBe("false");
        });
        expect(screen.getByTestId("email").textContent).toBe("");
        expect(sessionStorage.getItem("template_access_token")).toBeNull();
        expect(refreshMock).toHaveBeenCalledTimes(1);
    });

    it("clears token and user even when logout API throws", async () => {
        // Given: bootstrap succeeds and logout endpoint later fails.
        sessionStorage.setItem("template_access_token", "existing-token");
        getConfigMock.mockResolvedValue({ login_enabled: true });
        meMock.mockResolvedValue(FULL_SYSTEM_SCENARIO.principal);
        logoutApiMock.mockRejectedValue(new Error("logout failed"));

        render(
            <AuthProvider>
                <AuthProbe />
            </AuthProvider>,
        );

        await waitFor(() => {
            expect(screen.getByTestId("loading").textContent).toBe("false");
        });

        // When: logout action is triggered.
        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: "logout" }));

        // Then: client session is cleared in finally branch.
        await waitFor(() => {
            expect(screen.getByTestId("email").textContent).toBe("");
        });
        expect(sessionStorage.getItem("template_access_token")).toBeNull();
        expect(logoutApiMock).toHaveBeenCalledTimes(1);
    });
});
