import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { DialogExample } from "../components/DialogExample";
import {
  Breadcrumb,
  Button,
  FormField,
  Pagination,
  ProvenancePanel,
  StatePanel,
  StatusBadge,
  Tabs,
  WorkspaceShell,
} from "../components/foundation";

describe("rendered FRONT-00 components", () => {
  test.each(["primary", "secondary", "quiet", "destructive"] as const)(
    "renders the %s button variant as a native button",
    (variant) => {
      render(<Button variant={variant}>{variant}</Button>);
      expect(screen.getByRole("button", { name: variant })).toHaveClass(
        `button--${variant}`,
      );
    },
  );

  test("renders a disabled button", () => {
    render(<Button disabled>Nicht verbunden</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  test("status badge exposes text as well as its hidden marker", () => {
    render(<StatusBadge state="under_review">In Prüfung</StatusBadge>);
    expect(screen.getByText("In Prüfung")).toHaveAttribute(
      "data-state",
      "under_review",
    );
  });

  test("breadcrumb and tabs expose their current page", () => {
    render(
      <>
        <Breadcrumb
          items={[{ href: "/", label: "Start" }, { label: "Jetzt" }]}
        />
        <Tabs
          items={[
            { href: "#a", label: "Aktiv", current: true },
            { href: "#b", label: "Andere" },
          ]}
        />
      </>,
    );
    expect(screen.getByText("Jetzt").closest("li")).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Aktiv" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  test("field has label, hint, error and explicit described-by association", () => {
    render(
      <FormField
        id="title"
        label="Titel"
        hint="Kurzer Titel"
        error="Erforderlich"
      >
        <input aria-describedby="title-hint title-error" id="title" />
      </FormField>,
    );
    const input = screen.getByLabelText("Titel");
    expect(input).toHaveAccessibleDescription("Kurzer Titel Erforderlich");
    expect(screen.getByRole("alert")).toHaveTextContent("Erforderlich");
  });

  test("loading state is a live region", () => {
    render(
      <StatePanel state="loading" title="Lädt">
        Inhalt
      </StatePanel>,
    );
    expect(screen.getByText("Lädt").closest("section")).toHaveAttribute(
      "aria-live",
      "polite",
    );
  });

  test("workspace shell renders landmarks, navigation and skip link", () => {
    render(<WorkspaceShell workspaceId="WS-01">Inhalt</WorkspaceShell>);
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Hauptnavigation" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Zum Inhalt springen" }),
    ).toHaveAttribute("href", "#main-content");
  });

  test("provenance includes a correction link", () => {
    render(
      <ProvenancePanel
        correctionHref="/correction"
        source="Quelle"
        version="1"
      />,
    );
    expect(
      screen.getByRole("link", { name: "Korrektur melden" }),
    ).toHaveAttribute("href", "/correction");
  });

  test("pagination exposes current state and disabled boundaries", () => {
    render(<Pagination current={1} total={2} />);
    const navigation = screen.getByRole("navigation", {
      name: "Seitennavigation",
    });
    expect(within(navigation).getByText("Seite 1 von 2")).toBeInTheDocument();
    expect(
      within(navigation).getByRole("button", { name: "Zurück" }),
    ).toBeDisabled();
    expect(
      within(navigation).getByRole("button", { name: "Weiter" }),
    ).toBeEnabled();
  });

  test("dialog opens, moves focus, closes, returns focus and confirms", async () => {
    const user = userEvent.setup();
    const confirmed = vi.fn();
    render(<DialogExample onConfirm={confirmed} />);
    const opener = screen.getByRole("button", {
      name: "Bestätigung öffnen",
    });
    await user.click(opener);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("open");
    expect(screen.getByRole("button", { name: "Abbrechen" })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: "Abbrechen" }));
    expect(dialog).not.toHaveAttribute("open");
    expect(opener).toHaveFocus();
    await user.click(opener);
    await user.click(screen.getByRole("button", { name: "Verstanden" }));
    expect(confirmed).toHaveBeenCalledOnce();
    expect(opener).toHaveFocus();
  });
});
