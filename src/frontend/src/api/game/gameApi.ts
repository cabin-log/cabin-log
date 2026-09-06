import type { components } from "../generated/openapi";
import { apiClient, getAuthHeader } from "../http";

export type GameState = components["schemas"]["GameStateResponse"];
export type RewardPackage = components["schemas"]["RewardPackageResponse"];
export type RewardPackageClaim = components["schemas"]["RewardPackageClaimResponse"];
export type GameInventory = components["schemas"]["GameInventoryResponse"];
export type GameCollection = components["schemas"]["GameCollectionResponse"];
export type DailyRewardPackage = components["schemas"]["DailyRewardPackageResponse"];
export type CabinPlacement = components["schemas"]["CabinPlacementResponse"];

export async function getGameState(): Promise<GameState> {
    const { data, error } = await apiClient.GET("/api/v1/game/state", {
        headers: getAuthHeader(),
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function createDailyRewardPackage(rewardDate?: string): Promise<DailyRewardPackage> {
    const { data, error } = await apiClient.POST("/api/v1/game/activity/daily-reward", {
        headers: getAuthHeader(),
        params: {
            query: {
                reward_date: rewardDate,
            },
        },
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function syncRewardPackages(): Promise<RewardPackage[]> {
    const { data, error } = await apiClient.POST("/api/v1/game/rewards/sync", {
        headers: getAuthHeader(),
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function claimRewardPackage(packageId: number): Promise<RewardPackageClaim> {
    const { data, error } = await apiClient.POST("/api/v1/rewards/packages/{package_id}/claim", {
        headers: getAuthHeader(),
        params: {
            path: {
                package_id: packageId,
            },
        },
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function getInventory(): Promise<GameInventory> {
    const { data, error } = await apiClient.GET("/api/v1/game/inventory", {
        headers: getAuthHeader(),
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function getCollection(): Promise<GameCollection> {
    const { data, error } = await apiClient.GET("/api/v1/game/collection", {
        headers: getAuthHeader(),
    });
    if (error || !data) {
        throw error;
    }
    return data;
}

export async function deleteCabinPlacement(placementId: number): Promise<void> {
    const { error } = await apiClient.DELETE("/api/v1/game/cabin/placements/{placement_id}", {
        headers: getAuthHeader(),
        params: {
            path: {
                placement_id: placementId,
            },
        },
    });
    if (error) {
        throw error;
    }
}
