"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { useScopeTransition } from "./useScopeTransition";
import type {
  ActorMode,
  ApplicantCase,
  CapabilityStatus,
  InitiativeDraft,
  Locale,
  MemberRuntime,
  Result,
} from "./types";

const labels = {
  de: {
    unavailable: "Verbindung zur zuständigen Laufzeit nicht verfügbar",
    retry: "Sicher erneut versuchen",
    help: "Alternativ erreichen Sie die Mitgliederstelle schriftlich.",
    restricted: "Dieser Bereich ist für Ihr Konto nicht freigegeben.",
    back: "Zum eigenen Antrag",
  },
  en: {
    unavailable: "Responsible runtime is unavailable",
    retry: "Retry safely",
    help: "Alternatively, contact the membership office in writing.",
    restricted: "This area is not available to your account.",
    back: "Back to your application",
  },
};
const memberNav = [
  ["/member/home", "Übersicht"],
  ["/member/membership", "Profil & Mitgliedsstatus"],
  ["/member/initiatives", "Meine Vorschläge"],
  ["/member/deliberation", "Programmwerkstatt"],
  ["/member/delegation", "Meine Stimmen & Delegation"],
  ["/member/assurance/authentication-session-assurance", "Sicherheit"],
];

export function MemberWorkspace({
  path,
  runtime,
  actor,
}: {
  path: string;
  runtime: MemberRuntime;
  actor: ActorMode;
}) {
  const params = useSearchParams();
  const locale: Locale = params.get("lang") === "en" ? "en" : "de";
  const [principalState, setPrincipalState] = useState<
    "loading" | "ready" | "failed"
  >(runtime.profile === "fixture" ? "ready" : "loading");
  const [resolvedActor, setResolvedActor] = useState<ActorMode>(
    runtime.profile === "fixture" ? actor : "anonymous",
  );
  useEffect(() => {
    if (runtime.profile === "fixture") {
      setResolvedActor(actor);
      setPrincipalState("ready");
      return;
    }
    let active = true;
    setResolvedActor("anonymous");
    setPrincipalState("loading");
    void runtime.principal.resolve().then((result) => {
      if (!active) return;
      if (!result.ok) {
        setResolvedActor("anonymous");
        setPrincipalState("failed");
        return;
      }
      setResolvedActor(result.value.actor);
      setPrincipalState("ready");
    });
    return () => {
      active = false;
    };
  }, [actor, runtime]);
  const effectiveActor = runtime.profile === "fixture" ? actor : resolvedActor;
  const scope = useScopeTransition(
    runtime.organizationScope,
    principalState === "ready" && effectiveActor === "member",
  );
  const isApplication =
    path === "/member/application" || path === "/member/membership/appeal";
  const denied = effectiveActor === "applicant" && !isApplication;
  const unavailable = principalState === "failed";
  const logoTarget =
    effectiveActor === "applicant" ? "/member/application" : "/member/home";
  return (
    <div className="app-shell member-shell">
      <a className="skip-link" href="#member-main">
        Zum Inhalt
      </a>
      <header className="site-header">
        <div className="workspace-heading">
          <Link className="logo" href={`${logoTarget}?lang=${locale}`}>
            EPD²
          </Link>
          <span>Bürgerbereich</span>
        </div>
        <div className="header-actions">
          <Link
            href={`${path}?lang=de`}
            lang="de"
            aria-current={locale === "de" ? "page" : undefined}
          >
            DE
          </Link>
          <span aria-hidden>·</span>
          <Link
            href={`${path}?lang=en`}
            lang="en"
            aria-current={locale === "en" ? "page" : undefined}
          >
            EN
          </Link>
        </div>
      </header>
      {!isApplication && effectiveActor === "member" && (
        <nav className="member-navigation" aria-label="Mitgliederbereich">
          {memberNav.map(([href, label]) => (
            <Link
              key={href}
              href={`${href}?lang=${locale}`}
              aria-current={path === href ? "page" : undefined}
            >
              {label}
            </Link>
          ))}
        </nav>
      )}
      <main id="member-main" className="main" tabIndex={-1}>
        {principalState === "loading" ? (
          <State
            title="LOADING"
            text="Autorisierung wird geprüft"
            help="Geschützte Inhalte bleiben bis zur serverseitigen Prüfung verborgen."
          />
        ) : unavailable ? (
          <State
            title="BLOCKED"
            text={labels[locale].unavailable}
            help={labels[locale].help}
          />
        ) : denied ? (
          <State
            title="Zugriff nicht möglich"
            text={labels[locale].restricted}
            help={labels[locale].help}
          >
            <Link
              className="button button--primary"
              href={`/member/application?lang=${locale}`}
            >
              {labels[locale].back}
            </Link>
          </State>
        ) : (
          <RouteContent path={path} runtime={runtime} scope={scope} />
        )}
      </main>
    </div>
  );
}

function State({
  title,
  text,
  help,
  children,
}: {
  title: string;
  text: string;
  help: string;
  children?: React.ReactNode;
}) {
  return (
    <section className="state-panel" role="status">
      <span className="status-badge">{title}</span>
      <h1>{text}</h1>
      <p>{help}</p>
      {children}
    </section>
  );
}
function Capability({
  status,
  owner,
  reason,
}: {
  status: string;
  owner: string;
  reason: string;
}) {
  return (
    <aside className="notice" role="status">
      <strong>{status}</strong>
      <p>{reason}</p>
      <small>
        Zuständig: {owner}. Nächster Schritt: akzeptierten Vertrag abwarten.
      </small>
    </aside>
  );
}

function useScoped<T>(
  scope: ReturnType<typeof useScopeTransition>,
  loader: (scopeRef: string, signal: AbortSignal) => Promise<Result<T>>,
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);
  useEffect(() => {
    const current = ++generation.current;
    setData(null);
    setError(null);
    if (!scope.contextReady || !scope.scope || !scope.contextVersion) return;
    const controller = new AbortController();
    void loader(scope.scope, controller.signal).then((result) => {
      if (controller.signal.aborted || current !== generation.current) return;
      if (result.ok) setData(result.value);
      else setError(result.error.safeMessage);
    });
    return () => controller.abort();
  }, [scope.contextReady, scope.scope, scope.contextVersion, loader]);
  return { data, error };
}

function RouteContent({
  path,
  runtime,
  scope,
}: {
  path: string;
  runtime: MemberRuntime;
  scope: ReturnType<typeof useScopeTransition>;
}) {
  const memberCoreLoader = useMemo(
    () => runtime.memberCore.read.bind(runtime.memberCore),
    [runtime],
  );
  const membershipLoader = useMemo(
    () => runtime.membership.read.bind(runtime.membership),
    [runtime],
  );
  const initiativesLoader = useMemo(
    () => runtime.initiatives.list.bind(runtime.initiatives),
    [runtime],
  );
  const deliberationLoader = useMemo(
    () => runtime.deliberation.list.bind(runtime.deliberation),
    [runtime],
  );
  const delegationLoader = useMemo(
    () => runtime.delegation.status.bind(runtime.delegation),
    [runtime],
  );
  const memberCore = useScoped(scope, memberCoreLoader);
  const membership = useScoped(scope, membershipLoader);
  const initiatives = useScoped(scope, initiativesLoader);
  const deliberation = useScoped(scope, deliberationLoader);
  const delegation = useScoped(scope, delegationLoader);

  if (path === "/member/application") return <Applicant runtime={runtime} />;
  if (path === "/member/membership/appeal")
    return (
      <>
        <Page
          title="Rechtsbehelf zur Mitgliedschaft"
          lead="Ihr eigener Verfahrensweg bleibt in diesem Bereich. Interne Bearbeitung im Compliance- und Rechtsbereich wird nicht geöffnet."
        />
        <Capability
          status="BLOCKED"
          owner="Mitgliedschaft / Compliance & Recht"
          reason="Rechtliche und operative Aktivierung ist nicht nachgewiesen."
        />
      </>
    );
  if (path === "/member/home")
    return (
      <>
        <Page
          title="Mein Bürgerbereich"
          lead="Persönliche Mitgliedschaft, eigene Vorschläge und regionale Beteiligung – jeweils nur im serverseitig freigegebenen Organisationsumfang."
        />
        <StatusNotice runtimeProfile={runtime.profile} />
        <ScopeSelector scope={scope} />
        {memberCore.error && (
          <Capability
            status="BLOCKED"
            owner="MemberCorePort"
            reason={memberCore.error}
          />
        )}
        {scope.contextReady && memberCore.data && (
          <>
            <div className="grid">
              <Card title="Profil & Mitgliedsstatus">
                {memberCore.data.status} · {memberCore.data.organization}
              </Card>
              <Card title="Meine Vorschläge">
                Eigene Initiativen und Arbeitsstände
              </Card>
              <Card title="Programmwerkstatt">
                Diskussion und nachvollziehbare Versionen
              </Card>
              <Card title="Abstimmungen">
                <strong>GEPLANT / NICHT AKTIVIERT</strong>
                <p>
                  Hier wird nur Verfügbarkeit angezeigt. Eine spätere
                  Stimmabgabe bleibt im getrennten Voting Client; keine
                  Stimmabgabe im Bürgerbereich.
                </p>
              </Card>
              <Card title="Meine Stimmen & Delegation">
                <strong>{memberCore.data.capabilities.delegation}</strong>
                <p>
                  Delegationssemantik und Laufzeitvertrag sind noch nicht
                  aktiviert.
                </p>
              </Card>
              <Card title="Kommunikation mit Gremien">
                <strong>PLANNED_LATER</strong>
                <p>
                  Mitgliederkommunikation bleibt ein eigener, geregelter
                  Kommunikationsbereich.
                </p>
              </Card>
              <Card title="Transparente Beteiligungshistorie">
                <strong>PLANNED_LATER</strong>
                <p>
                  Nur freigegebene persönliche bzw. öffentliche Projektionen;
                  keine Rohaktenkopie im Bürgerbereich.
                </p>
              </Card>
              <Card title="Regionale Beteiligung">
                Autorisierter Umfang: {memberCore.data.organization}
              </Card>
            </div>
            <CrossWorkspaceLinks />
          </>
        )}
      </>
    );
  if (path === "/member/membership")
    return (
      <>
        <Page
          title="Profil & Mitgliedsstatus"
          lead="Mitgliedschaftsstatus, organisatorische Zuordnung und Korrekturweg. Identitätsprüfung allein aktiviert keine Mitgliedschaft."
        />
        {membership.error && (
          <Capability
            status="BLOCKED"
            owner="MembershipPort"
            reason={membership.error}
          />
        )}
        {membership.data && (
          <>
            <dl className="record">
              <dt>Status</dt>
              <dd>{membership.data.status}</dd>
              <dt>Zuordnung</dt>
              <dd>{membership.data.affiliation}</dd>
              <dt>Laufzeitvertrag</dt>
              <dd>{membership.data.version}</dd>
              <dt>Provenienz</dt>
              <dd>{membership.data.provenance}</dd>
            </dl>
            <h2>Verlauf</h2>
            <ol className="timeline">
              <li>Aufnahme bestätigt</li>
              <li>Zuordnung korrigiert</li>
            </ol>
            <Link
              className="button button--secondary"
              href="/member/membership/appeal"
            >
              Korrektur oder Rechtsbehelf
            </Link>
          </>
        )}
      </>
    );
  if (path === "/member/initiatives")
    return (
      <>
        <Page
          title="Meine Vorschläge"
          lead="Eigene Initiativen im aktuell autorisierten Organisationsumfang. Der Weg bleibt: Problem → Strukturierung → Diskussion → Fach-/Rechtsprüfung → demokratische Entscheidung → Dokumentation."
        />
        <ProgramDraftContext />
        <ScopeSelector scope={scope} />
        {initiatives.error && (
          <Capability
            status="BLOCKED"
            owner="InitiativesPort"
            reason={initiatives.error}
          />
        )}
        {scope.contextReady && initiatives.data && initiatives.data[0] && (
          <>
            <Card title="Offene kommunale Daten">
              {initiatives.data[0].state} · Version 4 ·{" "}
              {initiatives.data[0].scopeRef}
            </Card>
            <Link
              className="button button--primary"
              href="/member/initiatives/new"
            >
              Neue Initiative
            </Link>
          </>
        )}
      </>
    );
  if (path === "/member/initiatives/new")
    return scope.contextReady ? (
      <InitiativeFlow runtime={runtime} scopeRef={scope.scope} />
    ) : (
      <State
        title="LOADING"
        text="Autorisierte Organisation wird geladen"
        help="Ein Vorschlag kann erst nach erfolgreicher Scope-Autorisierung vorbereitet werden."
      />
    );
  if (path === "/member/deliberation")
    return (
      <>
        <Page
          title="Programmwerkstatt · Diskussion"
          lead="Beiträge mit Herkunft, Versionskontext und Sichtbarkeit. Diskussion ist eine Prozessphase und noch keine demokratische Entscheidung."
        />
        <ProgramDraftContext />
        <ProcessChain />
        {deliberation.error && (
          <Capability
            status="BLOCKED"
            owner="DeliberationPort"
            reason={deliberation.error}
          />
        )}
        {deliberation.data?.[0] && (
          <Card title="Offene kommunale Daten">
            <p>Sichtbar für den autorisierten Umfang {scope.scope}.</p>
            <small>
              Version 4 · Provenienz: {deliberation.data[0].provenance}
            </small>
          </Card>
        )}
      </>
    );
  if (path === "/member/delegation")
    return (
      <>
        <Page
          title="Meine Stimmen & Delegation"
          lead="Abstimmungsverfügbarkeit und Delegation werden getrennt von der eigentlichen Stimmabgabe dargestellt. Delegationsregeln werden nicht im Frontend erfunden."
        />
        <aside className="notice" role="status">
          <strong>Abstimmungen: GEPLANT / NICHT AKTIVIERT</strong>
          <p>
            eID und sichere Online-Abstimmungen sind Ziel-Fähigkeiten. Eine
            echte Stimmabgabe ist hier nicht verfügbar.
          </p>
        </aside>
        {delegation.error && (
          <Capability
            status="BLOCKED"
            owner="DelegationPort"
            reason={delegation.error}
          />
        )}
        {delegation.data && (
          <Capability
            status={delegation.data.activation}
            owner="Delegation domain"
            reason="Kein akzeptierter Laufzeitvertrag; daher kein aktives Formular."
          />
        )}
      </>
    );
  if (path === "/member/assurance/authentication-session-assurance")
    return (
      <>
        <Page
          title="Anmeldung, Sitzungen & Vertrauensarchitektur"
          lead="Darstellung der durch API‑02 gelieferten Assurance; keine eigene Authentifizierungsautorität."
        />
        <aside className="notice" role="status">
          <strong>eID: geplant, derzeit nicht live</strong>
          <p>
            Der Bürgerbereich startet keinen echten AusweisApp-Login.
            Identitätsprüfung und Mitgliedschaftsentscheidung bleiben getrennte
            Schritte.
          </p>
        </aside>
        {runtime.profile === "production" ? (
          <SessionAssurance runtime={runtime} />
        ) : (
          <Capability
            status="BLOCKED"
            owner="API‑02"
            reason="Sitzungs-, Passkey-, Widerrufs- und Recovery-Laufzeit ist bis zur unabhängigen API‑02-Annahme fail-closed."
          />
        )}
      </>
    );
  return (
    <State
      title="UNAVAILABLE"
      text="Seite nicht verfügbar"
      help="Der geschützte Datensatz wird nicht bestätigt oder verneint."
    />
  );
}

function Page({ title, lead }: { title: string; lead: string }) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">EPD² · Bürgerbereich</p>
        <h1>{title}</h1>
        <p>{lead}</p>
      </div>
    </header>
  );
}

function StatusNotice({
  runtimeProfile,
}: {
  runtimeProfile: MemberRuntime["profile"];
}) {
  return (
    <aside className="notice" role="status">
      <strong>Bürgerbereich im Aufbau</strong>
      {runtimeProfile === "fixture" ? (
        <p>
          FRONT‑03 ist eine PRE‑SEAL Arbeitsfassung. eID, sichere
          Online-Abstimmungen und nicht akzeptierte Laufzeitfunktionen werden
          nicht als live dargestellt.
        </p>
      ) : (
        <p>
          Die API‑02-C13-Sitzungs- und Autorisierungsgrenze ist angebunden.
          Nicht aktivierte Fachfunktionen, eID und Abstimmungen bleiben
          ausdrücklich gesperrt.
        </p>
      )}
    </aside>
  );
}

function SessionAssurance({ runtime }: { runtime: MemberRuntime }) {
  const [data, setData] = useState<{
    assurance: string;
    sessions: string[];
    passkeys: string[];
    recovery: CapabilityStatus;
  } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setData(null);
    setError("");
    void runtime.sessionAssurance.read().then((result) => {
      if (result.ok) setData(result.value);
      else setError(result.error.safeMessage);
    });
  }, [runtime]);
  if (error)
    return <Capability status="BLOCKED" owner="API‑02" reason={error} />;
  if (!data)
    return (
      <State
        title="LOADING"
        text="Sicherheitsstatus wird geladen"
        help="Es werden keine lokalen Bearer- oder Sitzungsgeheimnisse gespeichert."
      />
    );
  return (
    <div className="grid">
      <Card title="Assurance">{data.assurance}</Card>
      <Card title="Sitzungen">
        {data.sessions.length ? (
          <ul>
            {data.sessions.map((row) => (
              <li key={row}>{row}</li>
            ))}
          </ul>
        ) : (
          "Keine Sitzungsliste verfügbar"
        )}
      </Card>
      <Card title="Anmeldemittel">
        {data.passkeys.length ? (
          <ul>
            {data.passkeys.map((row) => (
              <li key={row}>{row}</li>
            ))}
          </ul>
        ) : (
          "Keine registrierten Anmeldemittel"
        )}
      </Card>
      <Capability
        status={data.recovery}
        owner="API‑02"
        reason="Recovery-/Re-enrollment-Aktionen sind in FRONT‑03 nicht als eigene Autorität implementiert."
      />
    </div>
  );
}

function ProgramDraftContext() {
  return (
    <aside className="notice" role="status">
      <strong>
        Grundsatzprogramm – Gründungsfassung 1.2 · Entwurf / noch nicht
        beschlossen
      </strong>
      <p>
        Vorschläge und Beratung in der Programmwerkstatt sind keine bereits
        angenommenen Programmpunkte. Die öffentliche Fassung bleibt eindeutig
        als Entwurf gekennzeichnet.
      </p>
      <a href="https://epd-partei.de/programm.html">
        Öffentlichen Programmstatus ansehen
      </a>
    </aside>
  );
}

function ProcessChain() {
  return (
    <section className="card" aria-labelledby="process-chain-title">
      <h2 id="process-chain-title" className="card-title">
        Weg eines Programmvorschlags
      </h2>
      <p>
        Problem → Strukturierung → Diskussion → Fach-/Rechtsprüfung →
        demokratische Entscheidung → Dokumentation
      </p>
    </section>
  );
}

function CrossWorkspaceLinks() {
  return (
    <section className="card" aria-labelledby="other-areas-title">
      <h2 id="other-areas-title" className="card-title">
        Weitere EPD²-Bereiche
      </h2>
      <p>
        Diese Konzepte bleiben öffentlich oder in anderen Arbeitsbereichen. Der
        Bürgerbereich übernimmt ihre operative Autorität nicht.
      </p>
      <ul>
        <li>
          <a href="https://epd-partei.de/transparenz.html">Transparenz</a> —
          öffentliche, freigegebene Darstellungen.
        </li>
        <li>
          <a href="https://epd-partei.de/transparenz/abgeordnetentisch.html">
            Offener Abgeordnetentisch
          </a>{" "}
          — öffentliche Rechenschaft, nicht Fallbearbeitung im Bürgerbereich.
        </li>
        <li>
          <a href="https://epd-partei.de/struktur/digitales-buero.html">
            Digitale Bürgerbüros
          </a>{" "}
          — eigener Bürgerbüro-/Fallbereich außerhalb des Bürgerbereichs.
        </li>
      </ul>
    </section>
  );
}
function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card">
      <h2 className="card-title">{title}</h2>
      {children}
    </section>
  );
}
function ScopeSelector({
  scope,
}: {
  scope: ReturnType<typeof useScopeTransition>;
}) {
  return (
    <section className="scope-control" aria-busy={scope.pending}>
      <label htmlFor="scope">Meine Organisation</label>
      <p className="muted">
        Bund · Landesverbände · Regional-/Ortsverbände. Angezeigt werden
        ausschließlich serverseitig autorisierte Umfänge.
      </p>
      <select
        id="scope"
        value={scope.scope}
        disabled={
          scope.pending || scope.loadingScopes || scope.scopes.length === 0
        }
        onChange={(e) => void scope.transition(e.target.value)}
      >
        {scope.scopes.map((candidate) => (
          <option key={candidate.ref} value={candidate.ref}>
            {candidate.label}
          </option>
        ))}
      </select>
      {scope.loadingScopes && (
        <span role="status">Autorisierte Organisationen werden geladen.</span>
      )}
      {scope.pending && (
        <span role="status">
          Berechtigung wird neu geprüft; vorherige Inhalte wurden entfernt.
        </span>
      )}
      {!scope.contextReady && !scope.pending && (
        <span role="alert">
          Zielumfang nicht aktiviert. Geschützte Inhalte bleiben verborgen.
        </span>
      )}
    </section>
  );
}

function Applicant({ runtime }: { runtime: MemberRuntime }) {
  const [data, setData] = useState<ApplicantCase | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setData(null);
    setError("");
    void runtime.applicantCase.readOwnCase().then((r) => {
      if (r.ok) setData(r.value);
      else setError(r.error.safeMessage);
    });
  }, [runtime]);
  if (error)
    return (
      <State
        title="BLOCKED"
        text="Antragsdetails sind noch nicht angebunden"
        help={error}
      />
    );
  if (!data)
    return (
      <State title="LOADING" text="Antrag wird geladen" help="Bitte warten." />
    );
  return (
    <>
      <Page
        title="Mein Aufnahmeantrag"
        lead="Eingereichte Informationen, Verfahrensstand und Ihre nächsten zulässigen Schritte. Antragstellerkonto und Mitgliedschaft sind getrennte Zustände."
      />
      <aside className="notice" role="status">
        <strong>Applicant ≠ Member</strong>
        <p>
          Identitätsprüfung oder Kontozugang allein begründen keine
          Mitgliedschaft. Erst eine autoritative Aufnahmeentscheidung kann den
          Mitgliedsstatus aktivieren.
        </p>
      </aside>
      <div className="grid">
        <Card title="Antrag">
          <strong>{data.reference}</strong>
          <p>Eingereicht: {data.submittedAt}</p>
        </Card>
        <Card title="Status">
          <strong>{data.status}</strong>
          <p>{data.stage}</p>
        </Card>
        <Card title="Zuständige Stelle">{data.unit}</Card>
        <Card title="Frist">{data.deadline}</Card>
      </div>
      <h2>Unterlagen</h2>
      <ul>
        {data.documents.map((x: string) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
      <h2>Verlauf</h2>
      <ol className="timeline">
        {data.timeline.map((x) => (
          <li key={x.at}>
            <time>{x.at}</time> {x.label}
          </li>
        ))}
      </ol>
      <aside className="notice">
        <h2>Offizielle Mitteilung</h2>
        <p>{data.notice}</p>
      </aside>
      <Link
        className="button button--secondary"
        href="/member/membership/appeal"
      >
        Korrektur / Rechtsbehelf
      </Link>
    </>
  );
}

function InitiativeFlow({
  runtime,
  scopeRef,
}: {
  runtime: MemberRuntime;
  scopeRef: string;
}) {
  const [step, setStep] = useState<
    "draft" | "preview" | "confirm" | "submitting" | "receipt" | "error"
  >("draft");
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [receipt, setReceipt] = useState("");
  const submitting = useRef(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const origin = useRef<HTMLButtonElement>(null);
  const draft: InitiativeDraft = {
    title,
    summary,
    clientRequestRef: "browser-generated-nonidentity-ref",
    expectedVersion: "1",
  };
  async function commit() {
    if (submitting.current) return;
    submitting.current = true;
    setStep("submitting");
    const principal = await runtime.principal.resolve();
    if (
      !principal.ok ||
      principal.value.actor !== "member" ||
      principal.value.assurance === "expired" ||
      principal.value.assurance === "revoked" ||
      principal.value.assurance === "step-up-required"
    ) {
      submitting.current = false;
      setStep("error");
      return;
    }
    const r = await runtime.initiatives.commit(scopeRef, draft);
    submitting.current = false;
    if (r.ok) {
      setReceipt(r.value.receiptRef);
      setStep("receipt");
      dialog.current?.close();
    } else setStep("error");
  }
  if (step === "receipt")
    return (
      <>
        <Page
          title="Initiative verbindlich übermittelt"
          lead="Erfolg wird erst nach autoritativer Commit-Bestätigung gezeigt."
        />
        <Card title="Quittung">
          <strong>{receipt}</strong>
          <p>Status: committed</p>
        </Card>
      </>
    );
  if (step === "error")
    return (
      <State
        title="BLOCKED"
        text="Übermittlung nicht bestätigt"
        help="Ohne autoritative Bestätigung wird kein Erfolg angezeigt."
      />
    );

  return (
    <>
      <Page
        title="Problem / Vorschlag einreichen"
        lead="Entwurf → Vorschau → ausdrückliche Bestätigung → autoritativer Commit → Quittung. Danach folgen Strukturierung, Diskussion und Prüfungen; ein Commit ist noch keine Annahme ins Programm."
      />
      <ProgramDraftContext />
      <ProcessChain />
      {step === "draft" ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setStep("preview");
          }}
        >
          <label>
            Titel
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <label>
            Kurzbeschreibung
            <textarea
              required
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
            />
          </label>
          <button className="button button--primary">Vorschau</button>
        </form>
      ) : (
        <Card title="Vorschau">
          <h2>{title}</h2>
          <p>{summary}</p>
          <button
            ref={origin}
            className="button button--primary"
            onClick={() => {
              setStep("confirm");
              dialog.current?.showModal();
            }}
          >
            Verbindlich übermitteln…
          </button>
        </Card>
      )}
      <dialog
        ref={dialog}
        onClose={() => origin.current?.focus()}
        aria-labelledby="confirm-title"
      >
        <h2 id="confirm-title">Übermittlung bestätigen</h2>
        <p>
          Die Initiative wird erst nach Bestätigung der zuständigen Laufzeit als
          erfolgreich angezeigt.
        </p>
        <button
          className="button button--secondary"
          onClick={() => {
            dialog.current?.close();
            setStep("preview");
          }}
        >
          Abbrechen
        </button>
        <button
          className="button button--primary"
          disabled={step === "submitting"}
          onClick={() => void commit()}
        >
          {step === "submitting" ? "Wird übermittelt…" : "Jetzt bestätigen"}
        </button>
      </dialog>
    </>
  );
}
