import type { components } from "../api/generated/openapi";

export type CabinGridContract = Pick<
    components["schemas"]["CabinResponse"],
    "width" | "depth" | "tile_width" | "tile_height" | "tile_z_height"
>;

export type CabinGridPoint = {
    x: number;
    y: number;
    z?: number;
};

export type CabinWorldPoint = {
    x: number;
    y: number;
};

export type CabinGridAnchor = {
    x: number;
    y: number;
};

export type CabinGridCellDiamond = {
    top: CabinWorldPoint;
    right: CabinWorldPoint;
    bottom: CabinWorldPoint;
    left: CabinWorldPoint;
};

export function getCabinGridAnchor(
    cabin: CabinGridContract,
    floorCenterX: number,
    floorCenterY: number,
): CabinGridAnchor {
    return {
        x: floorCenterX,
        y: floorCenterY - ((cabin.width + cabin.depth) * cabin.tile_height) / 4,
    };
}

export function projectCabinGridPoint(
    cabin: CabinGridContract,
    anchor: CabinGridAnchor,
    point: CabinGridPoint,
): CabinWorldPoint {
    const z = point.z ?? 0;

    return {
        x: anchor.x + (point.x - point.y) * (cabin.tile_width / 2),
        y: anchor.y + (point.x + point.y) * (cabin.tile_height / 2) - z * cabin.tile_z_height,
    };
}

export function getCabinGridCellDiamond(
    cabin: CabinGridContract,
    anchor: CabinGridAnchor,
    cell: CabinGridPoint,
): CabinGridCellDiamond {
    const top = projectCabinGridPoint(cabin, anchor, cell);
    const right = projectCabinGridPoint(cabin, anchor, { ...cell, x: cell.x + 1 });
    const bottom = projectCabinGridPoint(cabin, anchor, {
        ...cell,
        x: cell.x + 1,
        y: cell.y + 1,
    });
    const left = projectCabinGridPoint(cabin, anchor, { ...cell, y: cell.y + 1 });

    return { top, right, bottom, left };
}
