import { describe, expect, it } from "vitest";

import {
    getCabinGridAnchor,
    getCabinGridCellDiamond,
    projectCabinGridPoint,
    type CabinGridContract,
} from "../../../utils/cabinProjection";

const cabin: CabinGridContract = {
    width: 12,
    depth: 12,
    tile_width: 60,
    tile_height: 30,
    tile_z_height: 46,
};

function expectWorldPoint(point: { x: number; y: number }, x: number, y: number) {
    expect(point.x).toBeCloseTo(x);
    expect(point.y).toBeCloseTo(y);
}

describe("cabinProjection", () => {
    it("places the grid anchor above the floor center", () => {
        // Given: a 12x12 isometric grid and the visible floor center.
        const anchor = getCabinGridAnchor(cabin, 750, 362.3);

        // Then: the grid starts at the top of the floor diamond.
        expectWorldPoint(anchor, 750, 182.3);
    });

    it("projects grid coordinates into world coordinates", () => {
        // Given: the grid anchor has been aligned to the floor.
        const anchor = getCabinGridAnchor(cabin, 750, 362.3);

        // When/Then: x moves down-right, y moves down-left, and z lifts upward.
        expectWorldPoint(projectCabinGridPoint(cabin, anchor, { x: 1, y: 0 }), 780, 197.3);
        expectWorldPoint(projectCabinGridPoint(cabin, anchor, { x: 0, y: 1 }), 720, 197.3);
        expectWorldPoint(projectCabinGridPoint(cabin, anchor, { x: 1, y: 1, z: 1 }), 750, 166.3);
    });

    it("builds a cell diamond from four projected grid corners", () => {
        // Given: the top-left cell is projected.
        const anchor = getCabinGridAnchor(cabin, 750, 362.3);

        // When: the visual diamond for that cell is requested.
        const diamond = getCabinGridCellDiamond(cabin, anchor, { x: 0, y: 0 });

        // Then: its corners match one isometric tile.
        expectWorldPoint(diamond.top, 750, 182.3);
        expectWorldPoint(diamond.right, 780, 197.3);
        expectWorldPoint(diamond.bottom, 750, 212.3);
        expectWorldPoint(diamond.left, 720, 197.3);
    });
});
