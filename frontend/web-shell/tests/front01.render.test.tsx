import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  CapabilityStatusBanner,
  PublicPageView,
} from "../components/public-site";
import { publicPageByPath } from "../public/content";

describe("FRONT-01 public rendering", () => {
  it("renders accessible machine-readable capability status", () => {
    const page = publicPageByPath.get("/abstimmungen")!;
    render(<CapabilityStatusBanner page={page} />);
    const banner = screen.getByRole("region", {
      name: "Reifegrad dieser Fähigkeit",
    });
    expect(banner).toHaveAttribute("data-capability-status", "not_activated");
    expect(banner).toHaveAttribute("data-dependent-pack", page.pack);
    expect(banner).toHaveAttribute("data-workspace", "WS-01");
    expect(screen.getByText("Nicht aktiviert")).toBeInTheDocument();
  });

  it("renders exactly one public h1 and no operational form", () => {
    const { container } = render(
      <PublicPageView page={publicPageByPath.get("/")!} />,
    );
    expect(container.querySelectorAll("h1")).toHaveLength(1);
    expect(container.querySelector("header")).toBeInTheDocument();
    expect(container.querySelector("main")).toBeInTheDocument();
    expect(container.querySelector("footer")).toBeInTheDocument();
    expect(container.querySelector("form")).not.toBeInTheDocument();
  });

  it("renders all seven program states as read-only cards", () => {
    const { container } = render(
      <PublicPageView page={publicPageByPath.get("/programm/struktur")!} />,
    );
    expect(container.querySelectorAll("[data-program-state]")).toHaveLength(7);
    expect(
      screen.getByText(/Keine Eingabe, Unterstützung/),
    ).toBeInTheDocument();
  });
});
