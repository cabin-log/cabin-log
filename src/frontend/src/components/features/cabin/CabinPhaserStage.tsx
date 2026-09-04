import { ZoomIn, ZoomOut } from "lucide-react";
import { useEffect, useRef } from "react";

import { Tooltip } from "../../ui";
import {
    getCabinGridAnchor,
    getCabinGridCellDiamond,
    projectCabinGridPoint,
    type CabinGridContract,
} from "../../../utils/cabinProjection";

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

type CabinPhaserStageProps = {
    ariaLabel: string;
    cabin?: CabinGridContract | null;
    zoomControlsLabel: string;
    zoomInLabel: string;
    zoomOutLabel: string;
};

export function CabinPhaserStage({
    ariaLabel,
    cabin,
    zoomControlsLabel,
    zoomInLabel,
    zoomOutLabel,
}: CabinPhaserStageProps) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const zoomCameraRef = useRef<ZoomCamera | null>(null);
    const cabinGrid = cabin ?? DEFAULT_CABIN_GRID;

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
        cabinGrid.width,
    ]);

    return (
        <div
            ref={containerRef}
            className="cabin-phaser-stage"
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
