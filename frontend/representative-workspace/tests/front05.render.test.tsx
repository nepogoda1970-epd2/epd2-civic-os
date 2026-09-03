import { describe, expect, test } from "vitest";
import { render, screen, within } from "@testing-library/react";

import {
  CapabilityBadge,
  DependencyPanel,
  ErrorSummary,
  GovernedFallback,
  Notice,
  PageHeader,
  RefusalPanel,
  RevalidationNotice,
  StatusBadge,
} from "../components/primitives";
import { WS04_CONTENT } from "../content/de";
import { WS04_CAPABILITIES, capabilityRecord } from "../domain/capabilities";
import {
  RESTRICTED_REFUSAL,
  UNKNOWN_RESTRICTION_REFUSAL,
} from "../domain/conflict";
import { STALE_CASE, UNCERTAIN_CASE } from "../domain/caseWorkflow";
import {
  PROPOSAL_BLOCKED,
  PUBLICATION_MODEL_GAP,
  callerAssertedAuthorizationSufficient,
  mayPresentAsPublic,
} from "../domain/publication";
import { productionRefusal } from "../runtime/unavailable";

describe("the refusal panel", () => {
  test("states what happened, whether anything committed, and what to do", () => {
    render(
      <RefusalPanel title="Titel" refusal={productionRefusal("caseList")} />,
    );
    const panel = screen.getByRole("alert");
    expect(panel).toHaveAttribute(
      "data-refusal",
      "WS04_CASE_INTAKE_CONTRACT_NOT_ACCEPTED",
    );
    expect(
      within(panel).getByText(WS04_CONTENT.states.commitStatus),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText(WS04_CONTENT.states.committedNo),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText(WS04_CONTENT.states.nextStep),
    ).toBeInTheDocument();
  });

  test("an uncertain outcome is never rendered as a failure", () => {
    render(<RefusalPanel title="Titel" refusal={UNCERTAIN_CASE} />);
    expect(
      screen.getByText(WS04_CONTENT.states.committedUnknown),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(WS04_CONTENT.states.committedNo),
    ).not.toBeInTheDocument();
  });

  test("a stale-version conflict reports that nothing was committed", () => {
    render(<RefusalPanel title="Titel" refusal={STALE_CASE} />);
    expect(
      screen.getByText(WS04_CONTENT.states.committedNo),
    ).toBeInTheDocument();
  });

  test("a non-disclosing refusal is marked as such in the DOM", () => {
    render(<RefusalPanel title="Titel" refusal={RESTRICTED_REFUSAL} />);
    expect(screen.getByRole("alert")).toHaveAttribute(
      "data-non-disclosing",
      "true",
    );
  });

  test("the restricted and unknown-restriction refusals differ in disclosure", () => {
    expect(RESTRICTED_REFUSAL.nonDisclosing).toBe(true);
    expect(UNKNOWN_RESTRICTION_REFUSAL.nonDisclosing).toBe(false);
  });

  test("no refusal message contains a resource identifier", () => {
    for (const refusal of [
      productionRefusal("caseDetail"),
      RESTRICTED_REFUSAL,
      STALE_CASE,
      UNCERTAIN_CASE,
      PROPOSAL_BLOCKED,
    ]) {
      expect(refusal.safeMessage).not.toMatch(/[0-9]{4,}/);
      expect(refusal.safeMessage).not.toMatch(/PROTOTYP/);
    }
  });
});

describe("the capability badge", () => {
  test("never labels a blocked capability as available", () => {
    for (const record of WS04_CAPABILITIES) {
      const { unmount } = render(<CapabilityBadge status={record.status} />);
      const text = screen.getByText(/verfügbar|eingeschränkt|nicht vorgesehen/);
      if (record.status !== "SUPPORTED_REAL_PATH") {
        expect(text.textContent).not.toBe("verfügbar");
      }
      unmount();
    }
  });

  test("status is carried by text, not colour alone", () => {
    render(<StatusBadge label="nicht verfügbar" tone="blocked" />);
    expect(screen.getByText("nicht verfügbar")).toBeInTheDocument();
  });
});

describe("the dependency panel", () => {
  test("names the exact missing dependency", () => {
    const record = capabilityRecord("case_intake_list");
    render(
      <DependencyPanel
        title="Nicht abrufbar"
        dependency={record.missingDependency}
        behaviour={record.frontendBehaviour}
      />,
    );
    expect(screen.getByText(record.missingDependency)).toBeInTheDocument();
    expect(
      screen.getByText(WS04_CONTENT.states.dependency),
    ).toBeInTheDocument();
  });

  test("every blocked capability has a dependency string worth rendering", () => {
    for (const record of WS04_CAPABILITIES) {
      if (record.status !== "BLOCKED_BY_DEPENDENCY") continue;
      expect(record.missingDependency.length).toBeGreaterThan(20);
    }
  });
});

describe("supporting primitives", () => {
  test("the error summary links to the field it describes", () => {
    render(
      <ErrorSummary
        title="Bitte prüfen"
        items={[{ id: "field-1", message: "Angabe fehlt" }]}
      />,
    );
    const link = screen.getByRole("link", { name: "Angabe fehlt" });
    expect(link).toHaveAttribute("href", "#field-1");
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  test("an empty error summary renders nothing", () => {
    const { container } = render(<ErrorSummary title="x" items={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  test("the governed fallback keeps the offline route visible", () => {
    render(<GovernedFallback />);
    expect(screen.getByText(WS04_CONTENT.fallback.body)).toBeInTheDocument();
  });

  test("the revalidation notice denies that a visible control is authority", () => {
    render(<RevalidationNotice />);
    const notice = screen.getByText(WS04_CONTENT.auth.revalidationNotice);
    expect(notice).toHaveAttribute("data-revalidation-notice");
    expect(notice.textContent).toMatch(/keine Berechtigung/);
  });

  test("a notice renders its heading and body", () => {
    render(
      <Notice kind="legal" title="Rechtlicher Hinweis">
        <p>Inhalt</p>
      </Notice>,
    );
    expect(
      screen.getByRole("heading", { name: "Rechtlicher Hinweis" }),
    ).toBeInTheDocument();
  });

  test("the page header renders a single level-one heading", () => {
    render(<PageHeader title="Übersicht" lead="Text" />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Übersicht",
    );
  });
});

describe("the publication surface's security finding", () => {
  test("the model gap is presented as a security finding, not a gap", () => {
    expect(PUBLICATION_MODEL_GAP.classification).toBe(
      "SECURITY_SENSITIVE_BOUNDARY",
    );
    expect(PUBLICATION_MODEL_GAP.securityFinding).toMatch(/self-asserted/);
    expect(PUBLICATION_MODEL_GAP.disposition).toMatch(/SECURITY-RELEVANT/);
  });

  test("an approved state with no deciding authority is not public", () => {
    // The transparency service records no decider, so a state read back from it
    // cannot distinguish an authority's approval from the proposer's own claim.
    expect(
      mayPresentAsPublic({
        proposalId: "p",
        sourceKind: "position",
        sourceId: "s",
        state: "approved_by_publication_authority",
        decidedBy: null,
        publicRenditionRef: "ref",
      }),
    ).toBe(false);
    expect(
      mayPresentAsPublic({
        proposalId: "p",
        sourceKind: "position",
        sourceId: "s",
        state: "approved_by_publication_authority",
        decidedBy: "Veröffentlichungsstelle",
        publicRenditionRef: null,
      }),
    ).toBe(false);
  });

  test("a caller-asserted authorization is never sufficient", () => {
    expect(callerAssertedAuthorizationSufficient()).toBe(false);
  });
});
