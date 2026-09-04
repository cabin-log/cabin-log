const CABIN_ENTRY_REVEAL_KEY = "cabinlog:cabin:v1:entry-reveal";

export function markCabinEntryReveal(): void {
    window.sessionStorage.setItem(CABIN_ENTRY_REVEAL_KEY, "true");
}

export function consumeCabinEntryReveal(): boolean {
    const shouldReveal = window.sessionStorage.getItem(CABIN_ENTRY_REVEAL_KEY) === "true";
    window.sessionStorage.removeItem(CABIN_ENTRY_REVEAL_KEY);
    return shouldReveal;
}
