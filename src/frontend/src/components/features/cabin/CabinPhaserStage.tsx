import { ZoomIn, ZoomOut } from "lucide-react";
import { useEffect, useRef } from "react";

import { Tooltip } from "../../ui";

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
const CAMERA_MIN_ZOOM = 0.9;
const CAMERA_MAX_ZOOM = 1.8;
const CAMERA_ZOOM_STEP = 0.12;
const CAMERA_KEYBOARD_ZOOM_SPEED = 0.00045;

type CameraControl = {
    update: (delta: number) => void;
};

type ZoomCamera = (direction: "in" | "out") => void;

type CabinPhaserStageProps = {
    ariaLabel: string;
    zoomControlsLabel: string;
    zoomInLabel: string;
    zoomOutLabel: string;
};

export function CabinPhaserStage({
    ariaLabel,
    zoomControlsLabel,
    zoomInLabel,
    zoomOutLabel,
}: CabinPhaserStageProps) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const zoomCameraRef = useRef<ZoomCamera | null>(null);

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
    }, []);

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
