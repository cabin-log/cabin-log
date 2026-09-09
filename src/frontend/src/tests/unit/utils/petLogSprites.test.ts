import { describe, expect, it } from "vitest";

import {
    getPetDirectionFrames,
    getPetDirectionFromGridDelta,
    getPetLogSpriteSheet,
    getPetLogSpriteSheetForRewardKey,
} from "../../../utils/petLogSprites";

describe("petLogSprites", () => {
    it("describes the default 32px Octocat sheet", () => {
        const sheet = getPetLogSpriteSheet("default-octocat");

        expect(sheet).toMatchObject({
            frameWidth: 32,
            frameHeight: 32,
            assetPath: "/sprites/aseprites/cat-Sheet.png",
            firstDirectionFrame: 10,
            directionFrameCount: 10,
        });
        expect(sheet?.baseFrames).toEqual({ sleep: [0, 1], lie: [2, 3], held: 4 });
    });

    it("maps each direction to two standing and eight walking frames", () => {
        const sheet = getPetLogSpriteSheet("default-octocat");

        expect(sheet).toBeDefined();
        expect(getPetDirectionFrames(sheet!, "left")).toEqual({
            standing: [10, 11],
            walking: [12, 13, 14, 15, 16, 17, 18, 19],
        });
        expect(getPetDirectionFrames(sheet!, "upRight")).toEqual({
            standing: [70, 71],
            walking: [72, 73, 74, 75, 76, 77, 78, 79],
        });
        expect(getPetDirectionFrames(sheet!, "downRight")).toEqual({
            standing: [80, 81],
            walking: [82, 83, 84, 85, 86, 87, 88, 89],
        });
    });

    it("chooses a direction from projected movement", () => {
        expect(getPetDirectionFromGridDelta(-10, 0)).toBe("upLeft");
        expect(getPetDirectionFromGridDelta(0, -10)).toBe("upRight");
        expect(getPetDirectionFromGridDelta(10, 10)).toBe("down");
        expect(getPetDirectionFromGridDelta(-10, 10)).toBe("left");
        expect(getPetDirectionFromGridDelta(10, 0)).toBe("downRight");
        expect(getPetDirectionFromGridDelta(0, 10)).toBe("downLeft");
    });

    it("resolves the backend reward key to the registered asset sheet", () => {
        expect(getPetLogSpriteSheetForRewardKey("default.octocat")).toBe(
            getPetLogSpriteSheet("default-octocat"),
        );
    });
});
