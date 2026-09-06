import { describe, expect, it } from "vitest";

import { markCabinDailySyncComplete, shouldRunCabinDailySync } from "../../../utils/cabinDailySync";

describe("cabinDailySync", () => {
    it("tracks one automatic daily sync per user and reward date", () => {
        // Given: a user has not opened the cabin for the reward date yet.
        expect(shouldRunCabinDailySync(7, "2026-09-06")).toBe(true);

        // When: the automatic daily sync completes.
        markCabinDailySyncComplete(7, "2026-09-06");

        // Then: the same user/date is skipped, but other dates still run.
        expect(shouldRunCabinDailySync(7, "2026-09-06")).toBe(false);
        expect(shouldRunCabinDailySync(7, "2026-09-07")).toBe(true);
        expect(shouldRunCabinDailySync(8, "2026-09-06")).toBe(true);
    });
});
