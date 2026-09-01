import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  AccessAvailabilityPanel,
  CredentialExchangeWaitingPanel,
  EligibilityStatePanel,
  HandoffDepartureNotice,
  IsolatedVotingShell,
} from "../components/voting-trust";

describe("PACK-15 voting trust rendition", () => {
  it("renders the isolated voting shell without a banner landmark", () => {
    const { container } = render(
      <IsolatedVotingShell>
        <h1>Abstimmungsbereich</h1>
      </IsolatedVotingShell>,
    );
    expect(screen.queryByRole("banner")).not.toBeInTheDocument();
    expect(container.querySelector("nav")).not.toBeInTheDocument();
    expect(container.querySelectorAll("main")).toHaveLength(1);
    expect(container.querySelector("main")).toHaveAttribute(
      "id",
      "main-content",
    );
    expect(container.querySelector("[data-workspace]")).toHaveAttribute(
      "data-workspace",
      "WS-03",
    );
    const skip = screen.getByRole("link", { name: "Zum Inhalt springen" });
    expect(skip).toHaveAttribute("href", "#main-content");
  });

  it("renders the German eligibility label and the state attribute", () => {
    const { container } = render(
      <EligibilityStatePanel state="eligibility_confirmed" />,
    );
    expect(
      screen.getByRole("heading", { name: "Teilnahmeberechtigt" }),
    ).toBeInTheDocument();
    const panel = container.querySelector("[data-participation-state]");
    expect(panel).toHaveAttribute(
      "data-participation-state",
      "eligibility_confirmed",
    );
  });

  it("renders a denial with its reason path and no casting language", () => {
    const { container } = render(
      <EligibilityStatePanel state="eligibility_denied" />,
    );
    expect(
      screen.getByText(/Widerspruch einlegen/, { selector: "li" }),
    ).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/abgestimmt|Stimme abgegeben/);
  });

  it("renders no countdown in the access availability panel", () => {
    const { container } = render(
      <AccessAvailabilityPanel
        expiresLabel="14.09.2026, 18:00 Uhr"
        state="access_available"
      />,
    );
    expect(container.textContent ?? "").not.toMatch(
      /\d+\s*(Sekunden|Minuten)\s*verbleiben/,
    );
    expect(container.querySelector("progress")).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 3, name: "Zugang verfügbar" }),
    ).toBeInTheDocument();
  });

  it("announces the queued state politely and without a position", () => {
    const { container } = render(
      <AccessAvailabilityPanel
        expiresLabel="14.09.2026, 18:00 Uhr"
        state="access_queued"
      />,
    );
    expect(container.textContent ?? "").not.toMatch(
      /Position\s*\d+|Platz\s*\d+|noch\s*\d+\s*(Sekunden|Minuten)/,
    );
  });

  it("exposes the exchange waiting panel as a polite status region", () => {
    render(<CredentialExchangeWaitingPanel />);
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
    expect(status).toHaveTextContent("Zugang wird erstellt");
    expect(status.querySelector("progress")).not.toBeInTheDocument();
  });

  it("renders both German departure choices as links, not a form", () => {
    const { container } = render(<HandoffDepartureNotice />);
    const proceed = screen.getByRole("link", { name: "Fortfahren" });
    expect(proceed).toHaveAttribute("href", "/vote");
    expect(screen.getByRole("link", { name: "Abbrechen" })).toBeInTheDocument();
    expect(container.querySelector("form")).not.toBeInTheDocument();
    expect(
      screen.getByText(/Mir ist bekannt, dass ich den Abstimmungsbereich/),
    ).toBeInTheDocument();
  });
});
