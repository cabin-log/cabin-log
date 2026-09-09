import { ZoomIn, ZoomOut } from "lucide-react";
import { useEffect, useRef } from "react";

import { Tooltip } from "../../ui";
import {
    getCabinGridAnchor,
    getCabinGridCellDiamond,
    projectCabinGridPoint,
    type CabinGridContract,
    type CabinWorldPoint,
} from "../../../utils/cabinProjection";
import {
    getPetDirectionFrames,
    getPetDirectionFromGridDelta,
    getPetLogSpriteSheetForRewardKey,
    PET_SPRITE_DIRECTIONS,
    type PetLogSpriteSheetDefinition,
    type PetSpriteDirection,
} from "../../../utils/petLogSprites";
import type { CabinPlacement } from "../../../api/game/gameApi";

type PhaserModule = typeof import("phaser");

const CABIN_GAME_WIDTH = 1280;
const CABIN_GAME_HEIGHT = 720;
const CABIN_WORLD_WIDTH = 1500;
const CABIN_WORLD_HEIGHT = 800;
const FLOOR_TEXTURE_KEY = "cabin-floor-oak";
const WALL_TEXTURE_KEY = "cabin-wall-wood";
const FLOOR_ASSET_PATH = "/sprites/img/floor.png";
const WALL_ASSET_PATH = "/sprites/img/wall.png";
const ROOM_SCALE = 2.85;
const CABIN_WORLD_CENTER_X = CABIN_WORLD_WIDTH / 2;
const CABIN_WORLD_CENTER_Y = CABIN_WORLD_HEIGHT / 2 - 150;
const WALL_CENTER_Y = CABIN_WORLD_CENTER_Y - 89.7;
const FLOOR_CENTER_Y = CABIN_WORLD_CENTER_Y + 112.3;
const CABIN_GRID_ANCHOR_OFFSET_X = 0;
const CABIN_GRID_ANCHOR_OFFSET_Y = 0;
const CABIN_GRID_DEBUG_Z_LEVELS = 3;
const CAMERA_MIN_ZOOM = 0.9;
const CAMERA_MAX_ZOOM = 1.8;
const CAMERA_ZOOM_STEP = 0.12;
const CAMERA_KEYBOARD_ZOOM_SPEED = 0.00045;
const DEFAULT_CABIN_GRID: CabinGridContract = {
    width: 12,
    depth: 12,
    tile_width: 60,
    tile_height: 30,
    tile_z_height: 46,
};

type CameraControl = {
    update: (delta: number) => void;
};

type ZoomCamera = (direction: "in" | "out") => void;

type CabinStageContract = CabinGridContract & {
    placements?: CabinPlacement[];
};

type PendingStagePlacement = {
    key: string;
    title: string;
    assetKey: string;
};

type PetActor = {
    sprite: Phaser.GameObjects.Sprite;
    definition: PetLogSpriteSheetDefinition;
    home: { x: number; y: number; z: number };
    current: { x: number; y: number; z: number };
    target: { x: number; y: number; z: number };
    nextTargetAt: number;
    speed: number;
    currentSpeed: number;
    direction: PetSpriteDirection;
    isMoving: boolean;
};

type CabinPhaserStageProps = {
    ariaLabel: string;
    cabin?: CabinStageContract | null;
    pendingPlacement?: PendingStagePlacement | null;
    onPlacementCellClick?: (cell: { x: number; y: number }) => void;
    zoomControlsLabel: string;
    zoomInLabel: string;
    zoomOutLabel: string;
};

export function CabinPhaserStage({
    ariaLabel,
    cabin,
    pendingPlacement,
    onPlacementCellClick,
    zoomControlsLabel,
    zoomInLabel,
    zoomOutLabel,
}: CabinPhaserStageProps) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const zoomCameraRef = useRef<ZoomCamera | null>(null);
    const cabinGrid: CabinStageContract = cabin ?? { ...DEFAULT_CABIN_GRID, placements: [] };
    const cabinPlacementSignature = (cabinGrid.placements ?? [])
        .map((placement) =>
            [
                placement.id,
                placement.object_key,
                placement.x,
                placement.y,
                placement.z,
                placement.width,
                placement.depth,
            ].join(":"),
        )
        .join("|");
    const pendingPlacementSignature = pendingPlacement
        ? `${pendingPlacement.key}:${pendingPlacement.assetKey}`
        : "";
    const onPlacementCellClickRef =
        useRef<CabinPhaserStageProps["onPlacementCellClick"]>(undefined);

    useEffect(() => {
        onPlacementCellClickRef.current = onPlacementCellClick;
    }, [onPlacementCellClick]);

    useEffect(() => {
        if (import.meta.env.MODE === "test" || !containerRef.current) {
            return undefined;
        }

        let disposed = false;
        let game: InstanceType<PhaserModule["Game"]> | null = null;

        const boot = async () => {
            const Phaser = await import("phaser");
            if (disposed || !containerRef.current) {
                return;
            }

            class CabinFloorScene extends Phaser.Scene {
                private cameraControl?: CameraControl;

                private draggingCamera = false;

                private lastPointerX = 0;

                private lastPointerY = 0;

                private zoomInKey?: Phaser.Input.Keyboard.Key;

                private zoomOutKey?: Phaser.Input.Keyboard.Key;

                private gridAnchor = { x: 0, y: 0 };

                private petActors: PetActor[] = [];

                private heldPlacement?: Phaser.GameObjects.Sprite;

                private readonly handleCanvasWheel = (event: WheelEvent) => {
                    event.preventDefault();

                    const canvasBounds = this.game.canvas.getBoundingClientRect();
                    const pointerX =
                        ((event.clientX - canvasBounds.left) / canvasBounds.width) *
                        CABIN_GAME_WIDTH;
                    const pointerY =
                        ((event.clientY - canvasBounds.top) / canvasBounds.height) *
                        CABIN_GAME_HEIGHT;

                    this.zoomCameraAt(pointerX, pointerY, event.deltaY);
                };

                constructor() {
                    super("CabinFloorScene");
                }

                preload() {
                    this.load.image(FLOOR_TEXTURE_KEY, FLOOR_ASSET_PATH);
                    this.load.image(WALL_TEXTURE_KEY, WALL_ASSET_PATH);
                    const pendingDefinition = pendingPlacement
                        ? getPetLogSpriteSheetForRewardKey(pendingPlacement.assetKey)
                        : undefined;
                    const placementDefinitions = (cabinGrid.placements ?? [])
                        .map((placement) => getPetLogSpriteSheetForRewardKey(placement.object_key))
                        .filter(
                            (definition): definition is PetLogSpriteSheetDefinition =>
                                definition !== undefined,
                        );
                    const definitions = [pendingDefinition, ...placementDefinitions].filter(
                        (definition): definition is PetLogSpriteSheetDefinition =>
                            definition !== undefined,
                    );
                    for (const definition of definitions) {
                        if (!this.textures.exists(definition.textureKey)) {
                            this.load.spritesheet(definition.textureKey, definition.assetPath, {
                                frameWidth: definition.frameWidth,
                                frameHeight: definition.frameHeight,
                            });
                        }
                    }
                }

                create() {
                    const camera = this.cameras.main;
                    camera.setBackgroundColor("#101416");
                    camera.setBounds(0, 0, CABIN_WORLD_WIDTH, CABIN_WORLD_HEIGHT);
                    camera.centerOn(CABIN_WORLD_CENTER_X, CABIN_WORLD_CENTER_Y);
                    camera.setZoom(1);

                    const wall = this.add.image(
                        CABIN_WORLD_CENTER_X,
                        WALL_CENTER_Y,
                        WALL_TEXTURE_KEY,
                    );
                    wall.setOrigin(0.5, 0.5);
                    wall.setDepth(20);
                    wall.setScale(ROOM_SCALE);

                    const floor = this.add.image(
                        CABIN_WORLD_CENTER_X,
                        FLOOR_CENTER_Y,
                        FLOOR_TEXTURE_KEY,
                    );
                    floor.setOrigin(0.5, 0.5);
                    floor.setDepth(10);
                    floor.setScale(ROOM_SCALE);

                    this.drawCabinGridOverlay();
                    this.createPetAnimations();
                    this.createPlacementActors();
                    this.createHeldPlacementActor();
                    this.configureCameraControls(Phaser);
                    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
                        this.game.canvas.removeEventListener("wheel", this.handleCanvasWheel);
                    });
                    zoomCameraRef.current = (direction) => {
                        this.zoomCamera(direction === "in" ? CAMERA_ZOOM_STEP : -CAMERA_ZOOM_STEP);
                    };
                }

                update(_time: number, delta: number) {
                    this.cameraControl?.update(delta);
                    this.updateKeyboardZoom(delta);
                    this.updateHeldPlacement();
                    this.updatePetActors(_time, delta);
                    this.clampCameraZoom();
                }

                private configureCameraControls(phaser: PhaserModule) {
                    const camera = this.cameras.main;
                    const keyboard = this.input.keyboard;

                    this.game.canvas.addEventListener("wheel", this.handleCanvasWheel, {
                        passive: false,
                    });

                    if (keyboard) {
                        const cursors = keyboard.createCursorKeys();
                        this.zoomInKey = keyboard.addKey("E");
                        this.zoomOutKey = keyboard.addKey("Q");

                        this.cameraControl = new phaser.Cameras.Controls.SmoothedKeyControl({
                            camera,
                            left: cursors.left,
                            right: cursors.right,
                            up: cursors.up,
                            down: cursors.down,
                            acceleration: 0.08,
                            drag: 0.0007,
                            maxSpeed: 1.1,
                        });
                    }

                    this.input.on("pointerdown", (pointer: Phaser.Input.Pointer) => {
                        if (pendingPlacement) {
                            const cell = this.resolvePointerGridCell(pointer);
                            if (cell) {
                                onPlacementCellClickRef.current?.(cell);
                            }
                            return;
                        }
                        this.draggingCamera = true;
                        this.lastPointerX = pointer.x;
                        this.lastPointerY = pointer.y;
                    });

                    this.input.on("pointermove", (pointer: Phaser.Input.Pointer) => {
                        if (!this.draggingCamera || !pointer.isDown) {
                            return;
                        }

                        camera.scrollX -= (pointer.x - this.lastPointerX) / camera.zoom;
                        camera.scrollY -= (pointer.y - this.lastPointerY) / camera.zoom;
                        this.lastPointerX = pointer.x;
                        this.lastPointerY = pointer.y;
                    });

                    this.input.on("pointerup", () => {
                        this.draggingCamera = false;
                    });

                    this.input.on("gameout", () => {
                        this.draggingCamera = false;
                    });
                }

                private drawCabinGridOverlay() {
                    const graphics = this.add.graphics();
                    graphics.setDepth(30);

                    const baseAnchor = getCabinGridAnchor(
                        cabinGrid,
                        CABIN_WORLD_CENTER_X,
                        FLOOR_CENTER_Y,
                    );
                    const anchor = {
                        x: baseAnchor.x + CABIN_GRID_ANCHOR_OFFSET_X,
                        y: baseAnchor.y + CABIN_GRID_ANCHOR_OFFSET_Y,
                    };
                    this.gridAnchor = anchor;

                    for (let y = 0; y < cabinGrid.depth; y += 1) {
                        for (let x = 0; x < cabinGrid.width; x += 1) {
                            const diamond = getCabinGridCellDiamond(cabinGrid, anchor, { x, y });
                            const isEvenCell = (x + y) % 2 === 0;
                            graphics.lineStyle(
                                1,
                                isEvenCell ? 0xaeead6 : 0xf2c76b,
                                isEvenCell ? 0.38 : 0.3,
                            );
                            graphics.beginPath();
                            graphics.moveTo(diamond.top.x, diamond.top.y);
                            graphics.lineTo(diamond.right.x, diamond.right.y);
                            graphics.lineTo(diamond.bottom.x, diamond.bottom.y);
                            graphics.lineTo(diamond.left.x, diamond.left.y);
                            graphics.closePath();
                            graphics.strokePath();
                        }
                    }

                    const top = projectCabinGridPoint(cabinGrid, anchor, { x: 0, y: 0 });
                    const right = projectCabinGridPoint(cabinGrid, anchor, {
                        x: cabinGrid.width,
                        y: 0,
                    });
                    const bottom = projectCabinGridPoint(cabinGrid, anchor, {
                        x: cabinGrid.width,
                        y: cabinGrid.depth,
                    });
                    const left = projectCabinGridPoint(cabinGrid, anchor, {
                        x: 0,
                        y: cabinGrid.depth,
                    });
                    const center = projectCabinGridPoint(cabinGrid, anchor, {
                        x: cabinGrid.width / 2,
                        y: cabinGrid.depth / 2,
                    });

                    graphics.lineStyle(3, 0xf7f4ea, 0.86);
                    graphics.beginPath();
                    graphics.moveTo(top.x, top.y);
                    graphics.lineTo(right.x, right.y);
                    graphics.lineTo(bottom.x, bottom.y);
                    graphics.lineTo(left.x, left.y);
                    graphics.closePath();
                    graphics.strokePath();

                    const originMarker = this.add.circle(top.x, top.y, 5, 0xf4d35e, 0.95);
                    originMarker.setDepth(31);
                    const originLabel = this.add.text(top.x + 10, top.y - 22, "0,0", {
                        color: "#f7f4ea",
                        fontFamily: "Inter, system-ui, sans-serif",
                        fontSize: "16px",
                        fontStyle: "800",
                        stroke: "#101416",
                        strokeThickness: 4,
                    });
                    originLabel.setDepth(31);

                    const centerMarker = this.add.star(
                        center.x,
                        center.y,
                        4,
                        4,
                        10,
                        0x7bdff2,
                        0.95,
                    );
                    centerMarker.setDepth(31);
                    centerMarker.setAngle(45);

                    const debugLabel = this.add.text(
                        center.x + 14,
                        center.y - 12,
                        `${cabinGrid.width} x ${cabinGrid.depth}`,
                        {
                            color: "#d8fff3",
                            fontFamily: "Inter, system-ui, sans-serif",
                            fontSize: "16px",
                            fontStyle: "800",
                            stroke: "#101416",
                            strokeThickness: 4,
                        },
                    );
                    debugLabel.setDepth(31);

                    this.drawCabinGridZGuides(graphics, anchor, [
                        { x: 0, y: 0 },
                        { x: cabinGrid.width / 2, y: cabinGrid.depth / 2 },
                        { x: cabinGrid.width, y: 0 },
                        { x: 0, y: cabinGrid.depth },
                    ]);
                }

                private createPlacementActors() {
                    const placements = cabinGrid.placements ?? [];
                    for (const placement of placements) {
                        const definition = getPetLogSpriteSheetForRewardKey(placement.object_key);
                        if (!definition) {
                            continue;
                        }
                        const home = {
                            x: placement.x + placement.width / 2,
                            y: placement.y + placement.depth / 2,
                            z: placement.z,
                        };
                        const actor = this.createPetActor(home, definition);
                        this.petActors.push(actor);
                    }
                }

                private createHeldPlacementActor() {
                    const definition = pendingPlacement
                        ? getPetLogSpriteSheetForRewardKey(pendingPlacement.assetKey)
                        : undefined;
                    if (!pendingPlacement || !definition) {
                        return;
                    }
                    this.heldPlacement = this.add
                        .sprite(0, 0, definition.textureKey, definition.baseFrames.held)
                        .setOrigin(0.5, 0.5)
                        .setScale(definition.displayScale);
                    this.heldPlacement.setDepth(120);
                    this.heldPlacement.setAlpha(0.88);
                    this.updateHeldPlacement();
                }

                private updateHeldPlacement() {
                    if (!this.heldPlacement || !pendingPlacement) {
                        return;
                    }
                    const pointer = this.input.activePointer;
                    const worldPoint = this.cameras.main.getWorldPoint(pointer.x, pointer.y);
                    this.heldPlacement.setPosition(worldPoint.x, worldPoint.y);
                    this.heldPlacement.setDepth(200);
                }

                private createPetAnimations() {
                    const definitions = (cabinGrid.placements ?? [])
                        .map((placement) => getPetLogSpriteSheetForRewardKey(placement.object_key))
                        .concat(
                            pendingPlacement
                                ? [getPetLogSpriteSheetForRewardKey(pendingPlacement.assetKey)]
                                : [],
                        )
                        .filter(
                            (definition): definition is PetLogSpriteSheetDefinition =>
                                definition !== undefined,
                        );
                    for (const definition of definitions) {
                        for (const state of ["sleep", "lie"] as const) {
                            const animationKey = this.getPetBaseAnimationKey(definition, state);
                            if (!this.anims.exists(animationKey)) {
                                this.anims.create({
                                    key: animationKey,
                                    frames: this.anims.generateFrameNumbers(definition.textureKey, {
                                        frames: definition.baseFrames[state],
                                    }),
                                    frameRate: 2,
                                    repeat: -1,
                                });
                            }
                        }
                        for (const direction of PET_SPRITE_DIRECTIONS) {
                            const frames = getPetDirectionFrames(definition, direction);
                            const animationKey = this.getPetAnimationKey(definition, direction);
                            if (!this.anims.exists(animationKey)) {
                                this.anims.create({
                                    key: animationKey,
                                    frames: this.anims.generateFrameNumbers(definition.textureKey, {
                                        frames: frames.walking,
                                    }),
                                    frameRate: 8,
                                    repeat: -1,
                                });
                            }
                        }
                    }
                }

                private getPetAnimationKey(
                    definition: PetLogSpriteSheetDefinition,
                    direction: PetSpriteDirection,
                ) {
                    return `${definition.textureKey}-walk-${direction}`;
                }

                private getPetBaseAnimationKey(
                    definition: PetLogSpriteSheetDefinition,
                    state: "sleep" | "lie",
                ) {
                    return `${definition.textureKey}-${state}`;
                }

                private createPetActor(
                    home: { x: number; y: number; z: number },
                    definition: PetLogSpriteSheetDefinition,
                ): PetActor {
                    const point = projectCabinGridPoint(cabinGrid, this.gridAnchor, home);
                    const direction: PetSpriteDirection = "down";
                    const standingFrames = getPetDirectionFrames(definition, direction).standing;
                    const sprite = this.add
                        .sprite(point.x, point.y, definition.textureKey, standingFrames[0])
                        .setOrigin(0.5, 1)
                        .setDepth(38 + home.x + home.y + home.z * 10)
                        .setScale(definition.displayScale);
                    return {
                        sprite,
                        definition,
                        home,
                        current: { ...home },
                        target: { ...home },
                        nextTargetAt: 1400,
                        speed: 0.0009,
                        currentSpeed: 0,
                        direction,
                        isMoving: false,
                    };
                }

                private updatePetActors(time: number, delta: number) {
                    for (const actor of this.petActors) {
                        if (time >= actor.nextTargetAt) {
                            actor.target = this.pickPetTarget(actor.home);
                            actor.nextTargetAt = time + 3200 + Math.random() * 2800;
                            if (Math.random() < 0.2) {
                                const idleState = Math.random() < 0.5 ? "sleep" : "lie";
                                actor.target = { ...actor.current };
                                actor.isMoving = false;
                                actor.sprite.play(
                                    this.getPetBaseAnimationKey(actor.definition, idleState),
                                );
                                actor.nextTargetAt = time + 2200 + Math.random() * 2200;
                            }
                        }

                        const distanceX = actor.target.x - actor.current.x;
                        const distanceY = actor.target.y - actor.current.y;
                        const distance = Math.hypot(distanceX, distanceY);
                        if (distance > 0.01) {
                            const direction = getPetDirectionFromGridDelta(distanceX, distanceY);
                            if (!actor.isMoving || actor.direction !== direction) {
                                actor.direction = direction;
                                actor.sprite.play(
                                    this.getPetAnimationKey(actor.definition, direction),
                                );
                            }
                            actor.isMoving = true;
                            const desiredSpeed =
                                distance < 0.8 ? actor.speed * (distance / 0.8) : actor.speed;
                            actor.currentSpeed +=
                                (desiredSpeed - actor.currentSpeed) * Math.min(1, delta / 420);
                            const step = Math.min(distance, actor.currentSpeed * delta);
                            actor.current.x += (distanceX / distance) * step;
                            actor.current.y += (distanceY / distance) * step;
                        }
                        if (distance <= 0.01 && actor.isMoving) {
                            actor.isMoving = false;
                            actor.currentSpeed = 0;
                            const standingFrames = getPetDirectionFrames(
                                actor.definition,
                                actor.direction,
                            ).standing;
                            actor.sprite.stop();
                            actor.sprite.setFrame(standingFrames[0]);
                        }

                        const point = projectCabinGridPoint(
                            cabinGrid,
                            this.gridAnchor,
                            actor.current,
                        );
                        actor.sprite.setPosition(point.x, point.y);
                        actor.sprite.setDepth(
                            38 + actor.current.x + actor.current.y + actor.current.z * 10,
                        );
                    }
                }

                private pickPetTarget(home: { x: number; y: number; z: number }) {
                    const angle = Math.random() * Math.PI * 2;
                    const distance = 1.5 + Math.random() * 2.2;
                    const offset = {
                        x: Math.cos(angle) * distance,
                        y: Math.sin(angle) * distance,
                    };
                    return {
                        x: Math.min(cabinGrid.width - 0.5, Math.max(0.5, home.x + offset.x)),
                        y: Math.min(cabinGrid.depth - 0.5, Math.max(0.5, home.y + offset.y)),
                        z: home.z,
                    };
                }

                private resolvePointerGridCell(pointer: Phaser.Input.Pointer) {
                    const worldPoint = this.cameras.main.getWorldPoint(pointer.x, pointer.y);
                    const gridPoint = unprojectCabinWorldPoint(
                        cabinGrid,
                        this.gridAnchor,
                        worldPoint,
                    );
                    const x = Math.floor(gridPoint.x);
                    const y = Math.floor(gridPoint.y);
                    if (x < 0 || y < 0 || x >= cabinGrid.width || y >= cabinGrid.depth) {
                        return null;
                    }
                    return { x, y };
                }

                private drawCabinGridZGuides(
                    graphics: Phaser.GameObjects.Graphics,
                    anchor: { x: number; y: number },
                    guidePoints: Array<{ x: number; y: number }>,
                ) {
                    for (const guidePoint of guidePoints) {
                        const floorPoint = projectCabinGridPoint(cabinGrid, anchor, guidePoint);
                        const topPoint = projectCabinGridPoint(cabinGrid, anchor, {
                            ...guidePoint,
                            z: CABIN_GRID_DEBUG_Z_LEVELS,
                        });

                        graphics.lineStyle(2, 0xff6b6b, 0.74);
                        graphics.beginPath();
                        graphics.moveTo(floorPoint.x, floorPoint.y);
                        graphics.lineTo(topPoint.x, topPoint.y);
                        graphics.strokePath();

                        for (let z = 1; z <= CABIN_GRID_DEBUG_Z_LEVELS; z += 1) {
                            const levelPoint = projectCabinGridPoint(cabinGrid, anchor, {
                                ...guidePoint,
                                z,
                            });

                            const marker = this.add.circle(
                                levelPoint.x,
                                levelPoint.y,
                                4,
                                0xff6b6b,
                                0.92,
                            );
                            marker.setDepth(32);

                            const levelLabel = this.add.text(
                                levelPoint.x + 8,
                                levelPoint.y - 10,
                                `z=${z}`,
                                {
                                    color: "#ffd6d6",
                                    fontFamily: "Inter, system-ui, sans-serif",
                                    fontSize: "12px",
                                    fontStyle: "800",
                                    stroke: "#101416",
                                    strokeThickness: 3,
                                },
                            );
                            levelLabel.setDepth(32);
                        }
                    }
                }

                private updateKeyboardZoom(delta: number) {
                    if (this.zoomInKey?.isDown) {
                        this.zoomCamera(CAMERA_KEYBOARD_ZOOM_SPEED * delta);
                    }

                    if (this.zoomOutKey?.isDown) {
                        this.zoomCamera(-CAMERA_KEYBOARD_ZOOM_SPEED * delta);
                    }
                }

                private clampCameraZoom() {
                    const camera = this.cameras.main;
                    const nextZoom = Math.min(
                        CAMERA_MAX_ZOOM,
                        Math.max(this.getMinimumCameraZoom(), camera.zoom),
                    );

                    if (nextZoom !== camera.zoom) {
                        camera.setZoom(nextZoom);
                    }
                }

                private zoomCamera(delta: number) {
                    const camera = this.cameras.main;
                    const nextZoom = Math.min(
                        CAMERA_MAX_ZOOM,
                        Math.max(this.getMinimumCameraZoom(), camera.zoom + delta),
                    );

                    if (nextZoom !== camera.zoom) {
                        camera.setZoom(nextZoom);
                    }
                }

                private zoomCameraAt(pointerX: number, pointerY: number, deltaY: number) {
                    const camera = this.cameras.main;
                    const beforeZoom = camera.getWorldPoint(pointerX, pointerY);
                    this.zoomCamera(deltaY > 0 ? -CAMERA_ZOOM_STEP : CAMERA_ZOOM_STEP);
                    const afterZoom = camera.getWorldPoint(pointerX, pointerY);
                    camera.scrollX += beforeZoom.x - afterZoom.x;
                    camera.scrollY += beforeZoom.y - afterZoom.y;
                }

                private getMinimumCameraZoom() {
                    const camera = this.cameras.main;
                    return Math.max(
                        CAMERA_MIN_ZOOM,
                        camera.width / CABIN_WORLD_WIDTH,
                        camera.height / CABIN_WORLD_HEIGHT,
                    );
                }
            }

            game = new Phaser.Game({
                type: Phaser.AUTO,
                parent: containerRef.current,
                width: CABIN_GAME_WIDTH,
                height: CABIN_GAME_HEIGHT,
                backgroundColor: "#101416",
                pixelArt: true,
                antialias: false,
                roundPixels: true,
                scale: {
                    mode: Phaser.Scale.FIT,
                    autoCenter: Phaser.Scale.CENTER_BOTH,
                    width: CABIN_GAME_WIDTH,
                    height: CABIN_GAME_HEIGHT,
                },
                scene: CabinFloorScene,
            });
        };

        void boot();

        return () => {
            disposed = true;
            zoomCameraRef.current = null;
            game?.destroy(true);
        };
    }, [
        cabinGrid.depth,
        cabinGrid.tile_height,
        cabinGrid.tile_width,
        cabinGrid.tile_z_height,
        cabinPlacementSignature,
        pendingPlacementSignature,
        cabinGrid.width,
    ]);

    return (
        <div
            ref={containerRef}
            className={
                pendingPlacement
                    ? "cabin-phaser-stage cabin-phaser-stage--placing"
                    : "cabin-phaser-stage"
            }
            aria-label={ariaLabel}
            data-testid="cabin-phaser-stage"
        >
            <div
                className="cabin-phaser-stage__zoom-controls"
                role="group"
                aria-label={zoomControlsLabel}
            >
                <Tooltip content={zoomOutLabel} side="left">
                    <button
                        type="button"
                        className="cabin-phaser-stage__zoom-button"
                        onClick={() => zoomCameraRef.current?.("out")}
                        aria-label={zoomOutLabel}
                    >
                        <ZoomOut aria-hidden="true" />
                    </button>
                </Tooltip>
                <Tooltip content={zoomInLabel} side="left">
                    <button
                        type="button"
                        className="cabin-phaser-stage__zoom-button"
                        onClick={() => zoomCameraRef.current?.("in")}
                        aria-label={zoomInLabel}
                    >
                        <ZoomIn aria-hidden="true" />
                    </button>
                </Tooltip>
            </div>
        </div>
    );
}

function unprojectCabinWorldPoint(
    cabin: CabinGridContract,
    anchor: { x: number; y: number },
    point: CabinWorldPoint,
): { x: number; y: number } {
    const projectedX = (point.x - anchor.x) / (cabin.tile_width / 2);
    const projectedY = (point.y - anchor.y) / (cabin.tile_height / 2);
    return {
        x: (projectedY + projectedX) / 2,
        y: (projectedY - projectedX) / 2,
    };
}
