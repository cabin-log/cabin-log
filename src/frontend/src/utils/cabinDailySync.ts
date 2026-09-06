const CABIN_DAILY_SYNC_KEY_PREFIX = "cabinlog:cabin:v1:daily-sync";

function getCabinDailySyncKey(userId: number, rewardDate: string): string {
    return `${CABIN_DAILY_SYNC_KEY_PREFIX}:${userId}:${rewardDate}`;
}

export function shouldRunCabinDailySync(userId: number, rewardDate: string): boolean {
    return window.localStorage.getItem(getCabinDailySyncKey(userId, rewardDate)) !== "done";
}

export function markCabinDailySyncComplete(userId: number, rewardDate: string): void {
    window.localStorage.setItem(getCabinDailySyncKey(userId, rewardDate), "done");
}
