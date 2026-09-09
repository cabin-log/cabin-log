export const PET_SPRITE_DIRECTIONS = [
    "left",
    "upLeft",
    "downLeft",
    "down",
    "up",
    "right",
    "upRight",
    "downRight",
] as const;

export type PetSpriteDirection = (typeof PET_SPRITE_DIRECTIONS)[number];
export type PetSpriteBaseState = "sleep" | "lie" | "held";

export type PetLogSpriteSheetDefinition = {
    textureKey: string;
    assetPath: string;
    frameWidth: number;
    frameHeight: number;
    baseFrames: {
        sleep: number[];
        lie: number[];
        held: number;
    };
    firstDirectionFrame: number;
    directionFrameCount: number;
    standingFrameCount: number;
    walkingFrameCount: number;
    displayScale: number;
};

export const PET_LOG_SPRITE_SHEETS: Record<string, PetLogSpriteSheetDefinition> = {
    "default-octocat": {
        textureKey: "petlog-default-octocat",
        assetPath: "/sprites/aseprites/cat-Sheet.png",
        frameWidth: 32,
        frameHeight: 32,
        baseFrames: {
            sleep: [0, 1],
            lie: [2, 3],
            held: 4,
        },
        firstDirectionFrame: 10,
        directionFrameCount: 10,
        standingFrameCount: 2,
        walkingFrameCount: 8,
        displayScale: 2,
    },
};

export function getPetLogSpriteSheet(assetKey: string): PetLogSpriteSheetDefinition | undefined {
    return PET_LOG_SPRITE_SHEETS[assetKey];
}

export function getPetLogSpriteSheetForRewardKey(
    rewardKey: string,
): PetLogSpriteSheetDefinition | undefined {
    const assetKey = rewardKey === "default.octocat" ? "default-octocat" : rewardKey;
    return getPetLogSpriteSheet(assetKey);
}

export function getPetDirectionFrames(
    definition: PetLogSpriteSheetDefinition,
    direction: PetSpriteDirection,
) {
    const directionIndex = PET_SPRITE_DIRECTIONS.indexOf(direction);
    const blockStart =
        definition.firstDirectionFrame + directionIndex * definition.directionFrameCount;
    return {
        standing: Array.from(
            { length: definition.standingFrameCount },
            (_, index) => blockStart + index,
        ),
        walking: Array.from(
            { length: definition.walkingFrameCount },
            (_, index) => blockStart + definition.standingFrameCount + index,
        ),
    };
}

export function getPetDirectionFromGridDelta(deltaX: number, deltaY: number): PetSpriteDirection {
    const angle = Math.atan2(deltaY, deltaX);
    const octant = (Math.round(angle / (Math.PI / 4)) + 8) % 8;
    const directions: PetSpriteDirection[] = [
        "downRight",
        "down",
        "downLeft",
        "left",
        "upLeft",
        "up",
        "upRight",
        "right",
    ];
    return directions[octant] ?? "down";
}
