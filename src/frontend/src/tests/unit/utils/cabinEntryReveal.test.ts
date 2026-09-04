import { describe, expect, it } from "vitest";

import { consumeCabinEntryReveal, markCabinEntryReveal } from "../../../utils/cabinEntryReveal";

describe("cabinEntryReveal", () => {
    it("marks and consumes one cabin entry reveal", () => {
        // Given: an OAuth login flow is about to leave the frontend.
        markCabinEntryReveal();

        // When/Then: the next cabin load consumes the queued reveal once.
        expect(consumeCabinEntryReveal()).toBe(true);
        expect(consumeCabinEntryReveal()).toBe(false);
    });
});
