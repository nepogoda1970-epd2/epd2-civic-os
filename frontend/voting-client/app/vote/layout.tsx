import { JourneyProvider } from "../../components/JourneyProvider";
import { IsolatedVotingShell } from "../../components/shell";

/**
 * The `/vote` layout holds the journey provider, so a client-side step from the
 * ballot to the review keeps the voter's selections in memory while a reload or
 * a direct visit starts from nothing.  Nothing is written to any persistent
 * store to achieve that.
 */
export default function VoteLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <JourneyProvider>
      <IsolatedVotingShell breadcrumbLabel="Abstimmung">
        {children}
      </IsolatedVotingShell>
    </JourneyProvider>
  );
}
