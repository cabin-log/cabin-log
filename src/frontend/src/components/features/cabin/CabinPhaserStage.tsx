import { useEffect, useRef } from "react";

type PhaserModule = typeof import("phaser");

const CABIN_GAME_WIDTH = 1280;
const CABIN_GAME_HEIGHT = 720;
const FLOOR_TEXTURE_KEY = "cabin-floor-oak";
const WALL_TEXTURE_KEY = "cabin-wall-wood";
const FLOOR_ASSET_PATH = "/sprites/img/floor.png";
const WALL_ASSET_PATH = "/sprites/img/wall.png";
const ROOM_SCALE = 2.85;
const ROOM_CENTER_X = CABIN_GAME_WIDTH / 2;
const WALL_CENTER_Y = CABIN_GAME_HEIGHT * 0.347;
const FLOOR_CENTER_Y = CABIN_GAME_HEIGHT * 0.38 + 178;

type CabinPhaserStageProps = {
    ariaLabel: string;
};

export function CabinPhaserStage({ ariaLabel }: CabinPhaserStageProps) {
    const containerRef = useRef<HTMLDivElement | null>(null);

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
                constructor() {
                    super("CabinFloorScene");
                }

                preload() {
                    this.load.image(FLOOR_TEXTURE_KEY, FLOOR_ASSET_PATH);
                    this.load.image(WALL_TEXTURE_KEY, WALL_ASSET_PATH);
                }

                create() {
                    this.cameras.main.setBackgroundColor("#101416");

                    const wall = this.add.image(ROOM_CENTER_X, WALL_CENTER_Y, WALL_TEXTURE_KEY);
                    wall.setOrigin(0.5, 0.5);
                    wall.setDepth(20);
                    wall.setScale(ROOM_SCALE);

                    const floor = this.add.image(ROOM_CENTER_X, FLOOR_CENTER_Y, FLOOR_TEXTURE_KEY);
                    floor.setOrigin(0.5, 0.5);
                    floor.setDepth(10);
                    floor.setScale(ROOM_SCALE);
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
            game?.destroy(true);
        };
    }, []);

    return (
        <div
            ref={containerRef}
            className="cabin-phaser-stage"
            aria-label={ariaLabel}
            data-testid="cabin-phaser-stage"
        />
    );
}
