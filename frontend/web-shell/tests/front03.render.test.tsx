import { render, screen } from "@testing-library/react";
import type { AnchorHTMLAttributes, PropsWithChildren } from "react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MemberWorkspace } from "../member/MemberWorkspace";
import { createFixtureRuntime, createProductionRuntime } from "../member/runtime";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...p
  }: PropsWithChildren<
    AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }
  >) => (
    <a href={href} {...p}>
      {children}
    </a>
  ),
}));

const member = () => (
  <MemberWorkspace
    path="/member/home"
    runtime={createFixtureRuntime("member")}
    actor="member"
  />
);

describe("FRONT-03 route application", () => {
  it("renders Member Core navigation for Member", async () => {
    render(member());
    expect(
      screen.getByRole("heading", { name: "Mein Bürgerbereich" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("navigation")).toHaveTextContent("Meine Vorschläge");
  });
  it("keeps Applicant shell free of Member navigation", () => {
    render(
      <MemberWorkspace
        path="/member/application"
        runtime={createFixtureRuntime("applicant")}
        actor="applicant"
      />,
    );
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "EPD²" })).toHaveAttribute(
      "href",
      "/member/application?lang=de",
    );
  });
  it("refuses a direct Member URL for Applicant", () => {
    render(
      <MemberWorkspace
        path="/member/home"
        runtime={createFixtureRuntime("applicant")}
        actor="applicant"
      />,
    );
    expect(
      screen.getByText("Dieser Bereich ist für Ihr Konto nicht freigegeben."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Profilangaben prüfen/)).not.toBeInTheDocument();
  });
  it("marks delegation as blocked without active form", async () => {
    render(
      <MemberWorkspace
        path="/member/delegation"
        runtime={createFixtureRuntime("member")}
        actor="member"
      />,
    );
    expect(await screen.findByText("BLOCKED")).toBeInTheDocument();
    expect(screen.queryByRole("form")).not.toBeInTheDocument();
  });
  it("renders fail-closed production-like state", () => {
    render(
      <MemberWorkspace
        path="/member/home"
        runtime={createProductionRuntime()}
        actor="anonymous"
      />,
    );
    expect(
      screen.getByText("Verbindung zur zuständigen Laufzeit nicht verfügbar"),
    ).toBeInTheDocument();
  });
  it("requires preview before confirmation", async () => {
    const user = userEvent.setup();
    render(
      <MemberWorkspace
        path="/member/initiatives/new"
        runtime={createFixtureRuntime("member")}
        actor="member"
      />,
    );
    const title = await screen.findByLabelText("Titel");
    await user.type(title, "Eine Initiative");
    await user.type(
      screen.getByLabelText("Kurzbeschreibung"),
      "Eine nachvollziehbare Beschreibung",
    );
    await user.click(screen.getByRole("button", { name: "Vorschau" }));
    expect(
      screen.getByRole("heading", { name: "Eine Initiative" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Quittung")).not.toBeInTheDocument();
  });
  it("appeal never exposes a WS-07 link", () => {
    render(
      <MemberWorkspace
        path="/member/membership/appeal"
        runtime={createFixtureRuntime("applicant")}
        actor="applicant"
      />,
    );
    expect(
      screen.getByText(/Compliance- und Rechtsbereich wird nicht geöffnet/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /WS-07/i })).not.toBeInTheDocument();
  });
});
