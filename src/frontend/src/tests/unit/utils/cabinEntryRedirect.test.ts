import { describe, expect, it, vi } from "vitest";

import { redirectLoginSuccessToCabin } from "../../../utils/cabinEntryRedirect";

describe("redirectLoginSuccessToCabin", () => {
    it("replaces login success with cabin before the app renders", () => {
        // Given: the OAuth callback loaded the frontend on the success route.
        const location = { pathname: "/login/success" } as Location;
        const history = {
            state: { idx: 0 },
            replaceState: vi.fn(),
        } as unknown as History;

        // When: the app bootstrap normalizes the route.
        redirectLoginSuccessToCabin(location, history);

        // Then: the browser history points directly at the cabin and reveal state is queued.
        expect(history.replaceState).toHaveBeenCalledWith({ idx: 0 }, "", "/cabin");
        expect(window.sessionStorage.getItem("cabinlog:cabin:v1:entry-reveal")).toBe("true");
    });

    it("leaves other routes unchanged", () => {
        // Given: the app booted on an ordinary route.
        const location = { pathname: "/login" } as Location;
        const history = {
            state: null,
            replaceState: vi.fn(),
        } as unknown as History;

        // When: the app bootstrap checks the route.
        redirectLoginSuccessToCabin(location, history);

        // Then: no redirect is applied.
        expect(history.replaceState).not.toHaveBeenCalled();
    });
});
