import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { Route, Routes, useLocation } from "react-router-dom";

import { LandingPage } from "../../../../pages/main/LandingPage";
import { renderWithRouter } from "../../../utils/renderWithRouter";

function LocationProbe() {
    const location = useLocation();
    return <p data-testid="location">{location.pathname}</p>;
}

function renderLanding(loginEnabled: boolean) {
    return renderWithRouter(
        <Routes>
            <Route path="/" element={<LandingPage loginEnabled={loginEnabled} />} />
            <Route path="/login" element={<LocationProbe />} />
            <Route path="/show-case" element={<LocationProbe />} />
        </Routes>,
    );
}

describe("LandingPage", () => {
    it("uses the shared public navbar structure", () => {
        renderLanding(true);

        const nav = screen.getByRole("banner", { name: "Landing navigation" });
        expect(within(nav).getByText("Cabinlog")).toBeInTheDocument();
    });

    it("marks landing as started and routes to login when login is enabled", async () => {
        renderLanding(true);

        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: "Get started" }));

        await waitFor(() => {
            expect(screen.getByTestId("location")).toHaveTextContent("/login");
        });
        expect(window.localStorage.getItem("b4fastapi:landing:v1:started")).toBe("true");
    });

    it("marks landing as started and routes to showcase when login is disabled", async () => {
        renderLanding(false);

        const user = userEvent.setup();
        await user.click(screen.getByRole("button", { name: "Get started" }));

        await waitFor(() => {
            expect(screen.getByTestId("location")).toHaveTextContent("/show-case");
        });
        expect(window.localStorage.getItem("b4fastapi:landing:v1:started")).toBe("true");
    });
});
