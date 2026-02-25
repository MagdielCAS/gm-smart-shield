import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Home } from "./pages/Home";

describe("Home Page", () => {
	it("renders welcome message", () => {
		render(<Home />);
		expect(screen.getByText("Welcome to GM Smart Shield")).toBeInTheDocument();
	});
});
