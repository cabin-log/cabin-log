import { markCabinEntryReveal } from "./cabinEntryReveal";

const LOGIN_SUCCESS_PATH = "/login/success";
const CABIN_PATH = "/cabin";

export function redirectLoginSuccessToCabin(location: Location, history: History): void {
    if (location.pathname !== LOGIN_SUCCESS_PATH) {
        return;
    }

    markCabinEntryReveal();
    history.replaceState(history.state, "", CABIN_PATH);
}
