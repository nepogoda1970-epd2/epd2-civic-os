import { describe, expect, test } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AssistancePanel } from "../components/assistance";
import { IsolatedVotingShell } from "../components/shell";
import {
  CapabilityBadge,
  ErrorSummary,
  GovernedFallback,
  JourneyStatus,
  Notice,
  RefusalPanel,
} from "../components/primitives";
import { ReceiptView } from "../components/ReceiptSurface";
import { PRODUCTION_REFUSALS, refusal } from "../runtime/unavailable";
import { PROHIBITED_PREMATURE_SUCCESS_PHRASES } from "../domain/stateMachine";
import { JOURNEY_STATES } from "../domain/types";
import type { Receipt } from "../domain/types";
import { WS03_CONTENT } from "../content/de";

const RECEIPT: Receipt = {
  electionContextReference: "KONTEXT-0001",
  confirmationCode: "ABCDEFGH23456789",
  boardCheckpointReference: "CHECKPOINT-14",
  sealedBatchReference: "BATCH-2026-W36",
  publicationStatus: "ACCEPTED_PENDING_BATCH_COMMITMENT",
  verificationInstructions:
    "Prüfen Sie den Code auf der gesonderten Prüfseite.",
  receiptSchemaVersion: "1",
  countingStatus: "COUNTED_IF_PUBLISHED",
};

describe("the isolated shell", () => {
  test("renders one main landmark, a skip link and no navigation", () => {
    const { container } = render(
      <IsolatedVotingShell breadcrumbLabel="Abstimmung">
        <h1>Titel</h1>
      </IsolatedVotingShell>,
    );
    expect(container.querySelectorAll("main")).toHaveLength(1);
    expect(container.querySelectorAll("nav")).toHaveLength(0);
    expect(container.querySelectorAll('[data-workspace="WS-03"]')).toHaveLength(
      1,
    );
    expect(
      screen.getByRole("link", { name: "Zum Inhalt springen" }),
    ).toHaveAttribute("href", "#main");
  });

  test("shows the prototype boundary and the no-tally rule", () => {
    render(
      <IsolatedVotingShell breadcrumbLabel="Abstimmung">
        <p>Inhalt</p>
      </IsolatedVotingShell>,
    );
    expect(screen.getByText(/nicht zertifiziert/)).toBeInTheDocument();
    expect(screen.getByText(/keine Zwischenstände/)).toBeInTheDocument();
  });

  test("renders no member navigation, account menu or organisation switcher", () => {
    const { container } = render(
      <IsolatedVotingShell breadcrumbLabel="Abstimmung">
        <p>Inhalt</p>
      </IsolatedVotingShell>,
    );
    const text = container.textContent ?? "";
    for (const forbidden of [
      "Mitgliederbereich verwalten",
      "Abmelden",
      "Mein Konto",
      "Organisation wechseln",
      "Profil",
    ]) {
      expect(text).not.toContain(forbidden);
    }
  });
});

describe("the refusal panel", () => {
  test("always answers the four questions a voter has", () => {
    render(
      <RefusalPanel
        title="Nicht verfügbar"
        refusal={refusal(PRODUCTION_REFUSALS.submission)}
      />,
    );
    const panel = screen.getByRole("alert");
    expect(
      within(panel).getAllByText(/nichts abgegeben und nichts gezählt/).length,
    ).toBeGreaterThan(0);
    expect(
      within(panel).getByText(
        /Stimmberechtigung gilt nach derzeitigem Stand weiter/,
      ),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText(WS03_CONTENT.states.nextStep),
    ).toBeInTheDocument();
  });

  test("is honest when the outcome is unknown", () => {
    render(
      <RefusalPanel
        title="Unklar"
        refusal={refusal(PRODUCTION_REFUSALS.submissionStatus)}
      />,
    );
    expect(
      screen.getByText(WS03_CONTENT.states.committedUnknown),
    ).toBeInTheDocument();
    expect(
      screen.getByText(WS03_CONTENT.states.entitlementUnknown),
    ).toBeInTheDocument();
  });

  test("carries the reason code as data, never as prose the voter must read", () => {
    const { container } = render(
      <RefusalPanel title="X" refusal={refusal(PRODUCTION_REFUSALS.crypto)} />,
    );
    const panel = container.querySelector("[data-refusal]");
    expect(panel).toHaveAttribute(
      "data-refusal",
      "WS03_BALLOT_CRYPTO_RUNTIME_BLOCKED",
    );
    expect(panel?.textContent).not.toContain(
      "WS03_BALLOT_CRYPTO_RUNTIME_BLOCKED",
    );
  });
});

describe("the journey status", () => {
  test("never uses completed-cast language before an acceptance", () => {
    for (const state of JOURNEY_STATES) {
      if (["accepted", "receipt_available", "verified"].includes(state))
        continue;
      const { container, unmount } = render(<JourneyStatus state={state} />);
      const text = container.textContent ?? "";
      for (const phrase of PROHIBITED_PREMATURE_SUCCESS_PHRASES) {
        expect(text, `${state} / ${phrase}`).not.toContain(phrase);
      }
      unmount();
    }
  });

  test("announces politely and exposes the commit knowledge", () => {
    const { container } = render(
      <JourneyStatus state="submission_uncertain" />,
    );
    const status = container.querySelector("[data-journey-state]");
    expect(status).toHaveAttribute("aria-live", "polite");
    expect(status).toHaveAttribute("data-commit-knowledge", "unknown");
  });
});

describe("capability presentation", () => {
  test("a blocked capability is never labelled available", () => {
    for (const status of [
      "BLOCKED_RUNTIME_CONTRACT",
      "BLOCKED_CRYPTO",
      "BLOCKED_INFRA",
      "BLOCKED_LEGAL",
      "BLOCKED_SECURITY_REVIEW",
    ] as const) {
      const { container, unmount } = render(
        <CapabilityBadge status={status} />,
      );
      expect(container.textContent).toBe("nicht verfügbar");
      unmount();
    }
  });

  test("only an accepted runtime is labelled available", () => {
    const { container } = render(
      <CapabilityBadge status="AVAILABLE_ACCEPTED_RUNTIME" />,
    );
    expect(container.textContent).toBe("verfügbar");
  });

  test("state is not conveyed by colour alone", () => {
    const { container } = render(<CapabilityBadge status="BLOCKED_CRYPTO" />);
    // The marker is decorative; the text carries the meaning.
    expect(container.querySelector(".status-badge__marker")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
    expect((container.textContent ?? "").trim().length).toBeGreaterThan(0);
  });
});

describe("the receipt view", () => {
  test("renders the permitted fields and the grouped code", () => {
    render(<ReceiptView receipt={RECEIPT} />);
    expect(screen.getByText("ABCD-EFGH-2345-6789")).toBeInTheDocument();
    expect(screen.getByText("KONTEXT-0001")).toBeInTheDocument();
    expect(
      screen.getByText("ACCEPTED_PENDING_BATCH_COMMITMENT"),
    ).toBeInTheDocument();
  });

  test("renders nothing that is not a permitted field", () => {
    const contaminated = {
      ...RECEIPT,
      choice: "Antwortmöglichkeit A",
      member_id: "M-1",
      boardSequence: "41",
    } as unknown as Receipt;
    const { container } = render(<ReceiptView receipt={contaminated} />);
    const text = container.textContent ?? "";
    expect(text).not.toContain("Antwortmöglichkeit A");
    expect(text).not.toContain("M-1");
    expect(text).not.toContain("41");
  });

  test("does not encourage sharing", () => {
    render(<ReceiptView receipt={RECEIPT} />);
    expect(screen.getByText(/belegt keine Auswahl/)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /teilen|senden|drucken/i }),
    ).toBeNull();
  });
});

describe("assistance", () => {
  test("states the operator boundary and exposes it as data", async () => {
    const user = userEvent.setup();
    const { container } = render(<AssistancePanel />);
    await user.click(screen.getByRole("button"));
    const marker = container.querySelector(
      "[data-operator-may-view-selections]",
    );
    expect(marker).toHaveAttribute(
      "data-operator-may-view-selections",
      "false",
    );
    expect(marker).toHaveAttribute(
      "data-operator-may-change-selections",
      "false",
    );
    expect(screen.getByText(/weder sehen noch treffen/)).toBeInTheDocument();
  });

  test("is a disclosure with correct expanded state", async () => {
    const user = userEvent.setup();
    render(<AssistancePanel />);
    const toggle = screen.getByRole("button");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });

  test("receives no ballot state to leak", () => {
    // The component takes no props at all, so there is no path from a caller
    // to the voter's selections through it.
    expect(AssistancePanel.length).toBe(0);
  });
});

describe("shared primitives", () => {
  test("the error summary links each message to its field", () => {
    render(
      <ErrorSummary
        title="Bitte prüfen"
        items={[{ id: "feld-1", message: "Zu viele Auswahlen" }]}
      />,
    );
    expect(
      screen.getByRole("link", { name: "Zu viele Auswahlen" }),
    ).toHaveAttribute("href", "#feld-1");
  });

  test("an empty error summary renders nothing", () => {
    const { container } = render(<ErrorSummary title="X" items={[]} />);
    expect(container.firstChild).toBeNull();
  });

  test("the governed fallback is always available", () => {
    render(<GovernedFallback />);
    expect(screen.getByText(WS03_CONTENT.fallback.body)).toBeInTheDocument();
  });

  test("a notice is a labelled region with a heading", () => {
    render(
      <Notice title="Hinweis" kind="warning">
        <p>Inhalt</p>
      </Notice>,
    );
    expect(
      screen.getByRole("heading", { name: "Hinweis" }),
    ).toBeInTheDocument();
  });
});
