import Link from "next/link";

import {
  CandidateBanner,
  Card,
  Notice,
  WorkspaceShell,
} from "../../../components/foundation";
import {
  AccessAvailabilityPanel,
  EligibilityStatePanel,
  HandoffDepartureNotice,
  VotingContextCard,
} from "../../../components/voting-trust";
import { VOTING_CONTENT } from "../../../public/voting-content";

export const metadata = {
  title: "Teilnahme an Abstimmungen — EPD² Civic OS",
  description:
    "Teilnahmeberechtigung und Zugang zum Abstimmungsbereich, getrennt dargestellt. Statische Beispieldaten, keine Backend-Anbindung.",
};

/**
 * PACK-15 — WS-02 participation surface.
 *
 * Static sample data only; no fetch, no browser storage, no measurement.
 * This surface renders eligibility and access availability. It renders no
 * access value and no ballot or participation status, because the identity
 * domain neither receives nor may display one.
 */
const SAMPLE_CONTEXT = {
  contextName: "Programmabstimmung Herbst 2026",
  votingType: "Programmentscheidung, einstufig",
  scope: "Landesverband Beispiel",
  windowLabel: "01.09.2026 bis 15.09.2026",
  accessExpiresLabel: "14.09.2026, 18:00 Uhr",
} as const;

export default async function VotingParticipationPage() {
  return (
    <WorkspaceShell workspaceId="WS-02">
      <CandidateBanner />
      <h1>{VOTING_CONTENT.contextSummary.heading}</h1>
      <p>{VOTING_CONTENT.contextSummary.intro}</p>

      <VotingContextCard
        contextName={SAMPLE_CONTEXT.contextName}
        scope={SAMPLE_CONTEXT.scope}
        votingType={SAMPLE_CONTEXT.votingType}
        windowLabel={SAMPLE_CONTEXT.windowLabel}
      />

      <EligibilityStatePanel state="eligibility_confirmed" />

      <AccessAvailabilityPanel
        expiresLabel={SAMPLE_CONTEXT.accessExpiresLabel}
        state="access_available"
      />

      <HandoffDepartureNotice />

      <Card title={VOTING_CONTENT.dispute.title}>
        <p>{VOTING_CONTENT.dispute.text}</p>
        <p>{VOTING_CONTENT.dispute.note}</p>
        <p>
          <Link href={VOTING_CONTENT.dispute.href}>
            {VOTING_CONTENT.dispute.linkLabel}
          </Link>{" "}
          — {VOTING_CONTENT.dispute.activationNote}
        </p>
      </Card>

      <Card title={VOTING_CONTENT.assistance.title}>
        <p>{VOTING_CONTENT.assistance.text}</p>
        <p>{VOTING_CONTENT.assistance.limits}</p>
        <p>
          <Link href={VOTING_CONTENT.assistance.href}>
            {VOTING_CONTENT.assistance.linkLabel}
          </Link>{" "}
          — {VOTING_CONTENT.assistance.activationNote}
        </p>
      </Card>

      <Notice kind="information" title={VOTING_CONTENT.deliveryRefusal.title}>
        <p>{VOTING_CONTENT.deliveryRefusal.text}</p>
      </Notice>

      <Notice kind="information" title={VOTING_CONTENT.smallElectorate.title}>
        <p>{VOTING_CONTENT.smallElectorate.text}</p>
      </Notice>

      <Card title={VOTING_CONTENT.notOfferedHeading}>
        <dl className="metadata-list">
          {VOTING_CONTENT.notOffered.map((row) => (
            <div key={row.expectation}>
              <dt>{row.expectation}</dt>
              <dd>{row.text}</dd>
            </div>
          ))}
        </dl>
      </Card>
    </WorkspaceShell>
  );
}
