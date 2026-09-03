"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  emptyDraft,
  toggleOption as toggleOptionIn,
  clearContest as clearContestIn,
} from "../domain/ballot";
import { transition, type JourneyEvent } from "../domain/stateMachine";
import type {
  BallotDraft,
  BallotStyle,
  ElectionContext,
  JourneyState,
  SafeRefusal,
  VotingContext,
} from "../domain/types";
import type { VotingRuntime } from "../runtime/ports";
import { resolveVotingRuntime } from "../runtime/compose";

/**
 * The journey state, held in memory for the life of the mounted tree.
 *
 * This provider lives in the `/vote` layout, so a client-side step from the
 * ballot to the review keeps the voter's selections while a reload, a direct
 * visit or a closed tab loses them completely.  That asymmetry is the
 * requirement: selections are ephemeral, and there is no safe recovery that
 * does not persist something sensitive, so the voter is offered a clear restart
 * instead of a silent resurrection.
 *
 * Nothing here writes to localStorage, sessionStorage, IndexedDB, a cookie, the
 * URL, the page title or a telemetry payload.  There is no such call in this
 * file and the static validator asserts its absence.
 */

export type JourneyValue = {
  readonly state: JourneyState;
  readonly context: VotingContext | null;
  readonly election: ElectionContext | null;
  readonly style: BallotStyle | null;
  readonly draft: BallotDraft | null;
  readonly refusal: SafeRefusal | null;
  readonly busy: boolean;
  readonly profile: "production" | "governed_test" | "unresolved";
  readonly enter: () => Promise<void>;
  readonly openBallot: () => Promise<void>;
  readonly toggleOption: (contestId: string, optionId: string) => void;
  readonly clearContest: (contestId: string) => void;
  readonly openReview: () => void;
  readonly returnToBallot: () => void;
  readonly cancel: () => void;
  readonly attemptSubmission: (
    submissionClass: "final_cast" | "public_evidentiary_challenge",
  ) => Promise<void>;
  readonly attemptLocalCheck: () => Promise<void>;
};

const JourneyContext = createContext<JourneyValue | null>(null);

export function useJourney(): JourneyValue {
  const value = useContext(JourneyContext);
  if (!value) {
    throw new Error("useJourney used outside the WS-03 journey boundary");
  }
  return value;
}

export function JourneyProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<JourneyState>("not_started");
  const [context, setContext] = useState<VotingContext | null>(null);
  const [election, setElection] = useState<ElectionContext | null>(null);
  const [style, setStyle] = useState<BallotStyle | null>(null);
  const [draft, setDraft] = useState<BallotDraft | null>(null);
  const [refusal, setRefusal] = useState<SafeRefusal | null>(null);
  const [busy, setBusy] = useState(false);
  const [profile, setProfile] = useState<
    "production" | "governed_test" | "unresolved"
  >("unresolved");

  /** One in-flight consequential action at a time; a second click is ignored. */
  const inFlight = useRef(false);
  const runtimeRef = useRef<VotingRuntime | null>(null);

  const runtime = useCallback(async () => {
    if (!runtimeRef.current) {
      runtimeRef.current = await resolveVotingRuntime();
      setProfile(runtimeRef.current.profile);
    }
    return runtimeRef.current;
  }, []);

  const advance = useCallback((event: JourneyEvent) => {
    setState((current) => transition(current, event));
  }, []);

  const guarded = useCallback(async (run: () => Promise<void>) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    try {
      await run();
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }, []);

  const enter = useCallback(async () => {
    await guarded(async () => {
      const api = await runtime();
      const result = await api.handoff.consume(null);
      if (!result.ok) {
        setRefusal(result.error);
        return;
      }
      setRefusal(null);
      setContext(result.value);
      advance({ type: "handoff_accepted" });
    });
  }, [advance, guarded, runtime]);

  const openBallot = useCallback(async () => {
    await guarded(async () => {
      const api = await runtime();
      let votingContext = context;
      if (!votingContext) {
        const entered = await api.handoff.consume(null);
        if (!entered.ok) {
          setRefusal(entered.error);
          return;
        }
        votingContext = entered.value;
        setContext(votingContext);
        advance({ type: "handoff_accepted" });
      }
      const manifest = await api.electionManifest.read(votingContext);
      if (!manifest.ok) {
        setRefusal(manifest.error);
        return;
      }
      setElection(manifest.value);
      const ballotStyle = await api.ballotStyle.read(votingContext);
      if (!ballotStyle.ok) {
        setRefusal(ballotStyle.error);
        return;
      }
      setRefusal(null);
      setStyle(ballotStyle.value);
      setDraft(emptyDraft(ballotStyle.value));
      advance({ type: "ballot_opened" });
    });
  }, [advance, context, guarded, runtime]);

  const toggleOption = useCallback(
    (contestId: string, optionId: string) => {
      setDraft((current) =>
        current && style
          ? toggleOptionIn(style, current, contestId, optionId)
          : current,
      );
      advance({ type: "selection_changed" });
    },
    [advance, style],
  );

  const clearContest = useCallback(
    (contestId: string) => {
      setDraft((current) =>
        current ? clearContestIn(current, contestId) : current,
      );
      advance({ type: "selection_changed" });
    },
    [advance],
  );

  const openReview = useCallback(() => {
    advance({ type: "review_opened" });
  }, [advance]);

  const returnToBallot = useCallback(() => {
    advance({ type: "review_returned" });
  }, [advance]);

  const cancel = useCallback(() => {
    // Cancelling discards the draft.  Nothing was sent, so nothing is left.
    setDraft(null);
    setStyle(null);
    setRefusal(null);
    advance({ type: "cancelled" });
  }, [advance]);

  const attemptSubmission = useCallback(
    async (submissionClass: "final_cast" | "public_evidentiary_challenge") => {
      await guarded(async () => {
        const api = await runtime();
        if (!context) return;
        // The retry token is derived per attempt and never leaves this
        // function while submission is unavailable.  It is not stored.
        const retryToken = `${submissionClass}:${draft?.ballotStyleId ?? ""}`;
        const envelope = await api.crypto.prepareEnvelope(
          context,
          draft ?? { ballotStyleId: "", selections: [] },
        );
        if (!envelope.ok) {
          // The cryptographic dependency is unavailable, so nothing was sent.
          // The journey does not advance to `submitted`: no submission began.
          setRefusal(envelope.error);
          return;
        }
        const submitted = await api.submission.submit(
          context,
          submissionClass,
          retryToken,
        );
        if (!submitted.ok) {
          setRefusal(submitted.error);
        }
      });
    },
    [context, draft, guarded, runtime],
  );

  const attemptLocalCheck = useCallback(async () => {
    await guarded(async () => {
      const api = await runtime();
      if (!context) return;
      // A local diagnostic check is client-local by specification. It is
      // attempted through the cryptographic port and through nothing else, so
      // it can never become a network artefact.
      const result = await api.crypto.prepareEnvelope(
        context,
        draft ?? { ballotStyleId: "", selections: [] },
      );
      if (!result.ok) setRefusal(result.error);
    });
  }, [context, draft, guarded, runtime]);

  const value = useMemo<JourneyValue>(
    () => ({
      state,
      context,
      election,
      style,
      draft,
      refusal,
      busy,
      profile,
      enter,
      openBallot,
      toggleOption,
      clearContest,
      openReview,
      returnToBallot,
      cancel,
      attemptSubmission,
      attemptLocalCheck,
    }),
    [
      attemptLocalCheck,
      attemptSubmission,
      busy,
      cancel,
      clearContest,
      context,
      draft,
      election,
      enter,
      openBallot,
      openReview,
      profile,
      refusal,
      returnToBallot,
      state,
      style,
      toggleOption,
    ],
  );

  return (
    <JourneyContext.Provider value={value}>{children}</JourneyContext.Provider>
  );
}
