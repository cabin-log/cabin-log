import type { components } from "../generated/openapi";
import { apiClient, getAuthHeader } from "../http";

export type GameState = components["schemas"]["GameStateResponse"];
export type RewardPackage = components["schemas"]["RewardPackageResponse"];
export type DailyRewardPackage = components["schemas"]["DailyRewardPackageResponse"];

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
