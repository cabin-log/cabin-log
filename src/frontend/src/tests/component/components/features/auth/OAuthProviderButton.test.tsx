import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { OAuthProviderButton } from "../../../../../components/features/auth/OAuthProviderButton";

describe("OAuthProviderButton", () => {
    it("adds a GitHub account picker prompt before OAuth navigation", async () => {
        // Given: a GitHub OAuth button should request account selection.
        const onBeforeNavigate = vi.fn(() => false);
        render(
            <OAuthProviderButton
                provider="github"
                label="Sign in with GitHub again"
                startPath="/api/v1/auth/oauth/github/start"
                prompt="select_account"
                onBeforeNavigate={onBeforeNavigate}
            />,
        );

        // When: the action is clicked.
        await userEvent
            .setup()
            .click(screen.getByRole("button", { name: "Sign in with GitHub again" }));

        // Then: the backend OAuth start URL includes the account picker prompt.
        expect(onBeforeNavigate).toHaveBeenCalledWith(
            expect.stringContaining("/api/v1/auth/oauth/github/start?prompt=select_account"),
        );
    });
});
