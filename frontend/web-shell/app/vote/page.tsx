import { Notice } from "../../components/foundation";
import {
  AccessRedeemedPanel,
  CredentialExchangeWaitingPanel,
  IsolatedVotingShell,
} from "../../components/voting-trust";
import { VOTING_CONTENT } from "../../public/voting-content";

export const metadata = {
  title: "Abstimmungsbereich — EPD²",
  description:
    "Getrennter Abstimmungsbereich ohne Angaben zur Person und ohne Erhebung von Nutzungsdaten.",
};

/**
 * PACK-15 — isolated voting origin (WS-03).
 *
 * This page renders no identity, no navigation, no account menu, no
 * measurement and no access value. The one-time access is created inside
 * this area and redeemed there immediately; it is never displayed, stored
 * or offered for copying. The ballot itself is not part of this round.
 */
export default async function VotingOriginPage() {
  return (
    <IsolatedVotingShell>
      <h1>{VOTING_CONTENT.arrival.title}</h1>
      <p>{VOTING_CONTENT.arrival.body}</p>
      <p>{VOTING_CONTENT.departure.deliveryNote}</p>

      <CredentialExchangeWaitingPanel />

      <AccessRedeemedPanel />

      <Notice kind="information" title="Noch kein Stimmzettel">
        <p>{VOTING_CONTENT.redeemed.transition}</p>
        <p>
          Dieser Bereich zeigt ausschließlich den Übergang in den
          Abstimmungsbereich. Es wird hier weder ein Stimmzettel dargestellt
          noch eine Stimme entgegengenommen.
        </p>
      </Notice>

      <Notice kind="information" title="Wenn der Vorgang abbricht">
        <p>{VOTING_CONTENT.abort.body}</p>
        <p>{VOTING_CONTENT.abort.nextStep}</p>
      </Notice>
    </IsolatedVotingShell>
  );
}
