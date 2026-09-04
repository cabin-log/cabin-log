import type { components } from "../generated/openapi";
import { apiClient, getAuthHeader } from "../http";

export type GameState = components["schemas"]["GameStateResponse"];
export type RewardPackage = components["schemas"]["RewardPackageResponse"];

export async function getGameState(): Promise<GameState> {
    const { data, error } = await apiClient.GET("/api/v1/game/state", {
        headers: getAuthHeader(),
    });
    if (error || !data) {
        throw error;
    }
    return data;
}
