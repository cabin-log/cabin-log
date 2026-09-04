import { useMemo } from "react";

import * as gameApi from "../../../api/game/gameApi";
import { extractGameErrorDetail, resolveGameErrorMessage } from "../../../api/game/gameError";

export type { GameState, RewardPackage } from "../../../api/game/gameApi";

export function useGameApi() {
    return useMemo(
        () => ({
            ...gameApi,
            extractGameErrorDetail,
            resolveGameErrorMessage,
        }),
        [],
    );
}
