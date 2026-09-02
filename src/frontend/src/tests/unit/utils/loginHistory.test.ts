import { describe, expect, it } from "vitest";

import {
    getRecentLoginAccount,
    rememberRecentLoginAccount,
    toRecentLoginAccount,
} from "../../../utils/loginHistory";

describe("loginHistory", () => {
    it("stores and reads the latest GitHub login account", () => {
        // Given: a GitHub-connected user has logged in.
        const user = {
            id: 12,
            email: "octo@example.com",
            name: "Octo Dev",
            profile_image_url: "https://example.com/avatar.png",
            oauth_providers: ["github"],
        };

        // When: the user is remembered.
        const storedAccount = rememberRecentLoginAccount(user);

        // Then: display-safe account details can be restored later.
        expect(storedAccount).toMatchObject({
            userId: 12,
            email: "octo@example.com",
            name: "Octo Dev",
            profileImageUrl: "https://example.com/avatar.png",
            provider: "github",
        });
        expect(getRecentLoginAccount()).toMatchObject({
            userId: 12,
            email: "octo@example.com",
            name: "Octo Dev",
            provider: "github",
        });
    });

    it("does not remember non-GitHub users", () => {
        // Given: a user authenticated by a different provider.
        const user = {
            id: 12,
            email: "octo@example.com",
            name: "Octo Dev",
            profile_image_url: null,
            oauth_providers: ["google"],
        };

        // When: the account is converted for login history.
        const recentAccount = toRecentLoginAccount(user);

        // Then: no GitHub login shortcut is stored.
        expect(recentAccount).toBeNull();
        expect(rememberRecentLoginAccount(user)).toBeNull();
        expect(getRecentLoginAccount()).toBeNull();
    });

    it("ignores malformed stored login history", () => {
        // Given: storage contains an invalid record.
        window.localStorage.setItem("cabinlog:login:v1:recent-account", "{");

        // When: login history is read.
        const recentAccount = getRecentLoginAccount();

        // Then: the malformed value is ignored.
        expect(recentAccount).toBeNull();
    });
});
