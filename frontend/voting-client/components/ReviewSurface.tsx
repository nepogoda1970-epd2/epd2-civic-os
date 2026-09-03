"use client";

import Link from "next/link";
import { useEffect } from "react";

import { WS03_CONTENT } from "../content/de";
import { selectionFor } from "../domain/ballot";
import { capability } from "../domain/capabilities";
import { submissionPermittedFrom } from "../domain/stateMachine";
import { mayViewBallotSelections } from "../policies/supportRole";
import {
  CapabilityBadge,
  GovernedFallback,
  JourneyStatus,
  Notice,
  RefusalPanel,
} from "./primitives";
import { AssistancePanel } from "./assistance";
import { useJourney } from "./JourneyProvider";

/**
 * PAGE-018 — Stimme prüfen.
 *
 * Three separately named actions with three different consequences, presented
 * with equal weight and no default: the local check on this device, the public
 * evidentiary record, and the final cast.  None of them is styled as an error
 * path and none of them is reachable without the review having been opened.
 *
 * Nothing on this page claims a vote was cast.  The state machine does not
 * offer a transition to `accepted` that this component could take.
 */
export function ReviewSurface() {
  const journey = useJourney();

  // Reaching this page *is* opening the review, so the transition belongs here
  // rather than on the link that led here: a state change racing a navigation
  // is the kind of thing that would silently leave the consequential actions
  // unreachable, and the review step is not optional.
  useEffect(() => {
    journey.openReview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const style = journey.style;
  const draft = journey.draft;
  const cast = capability("ballot_submission");
  const crypto = capability("ballot_crypto");
  const localCheck = capability("local_diagnostic_challenge");
  const publicChallenge = capability("public_evidentiary_challenge");

  const canSubmit = submissionPermittedFrom(journey.state);
  const voterMayView = mayViewBallotSelections(
    journey.context?.role ?? "eligible_voter",
  );

  if (journey.state === "cancelled") {
    return (
      <>
        <div className="page-header">
          <h1>{WS03_CONTENT.review.title}</h1>
        </div>
        <JourneyStatus state={journey.state} />
        <Notice
          kind="information"
          title={WS03_CONTENT.review.cancelledTitle}
          role="status"
        >
          <p>{WS03_CONTENT.review.cancelledBody}</p>
          <p>
            <Link
              className="button button--secondary"
              href="/vote/credential"
              prefetch={false}
            >
              Erneut beginnen
            </Link>
          </p>
        </Notice>
        <GovernedFallback />
      </>
    );
  }

  return (
    <>
      <div className="page-header">
        <h1>{WS03_CONTENT.review.title}</h1>
        <p>{WS03_CONTENT.review.lead}</p>
      </div>

      <JourneyStatus state={journey.state} />

      {!style || !draft ? (
        <Notice kind="warning" title="Keine Auswahl vorhanden" role="alert">
          <p>
            Für diese Sitzung liegt keine Auswahl vor. Ihre Auswahl wird nicht
            gespeichert; nach einem Neuladen beginnen Sie erneut.
          </p>
          <p>{WS03_CONTENT.states.committedNo}</p>
          <p>
            <Link
              className="button button--secondary"
              href="/vote/credential"
              prefetch={false}
            >
              Erneut beginnen
            </Link>
          </p>
        </Notice>
      ) : (
        <>
          <section className="card">
            <h2 className="card-title">{WS03_CONTENT.review.yourSelection}</h2>
            {voterMayView ? (
              <ul className="selection-list">
                {style.contests.map((contest) => {
                  const selection = selectionFor(draft, contest.contestId);
                  const labels = contest.options
                    .filter((option) =>
                      selection.optionIds.includes(option.optionId),
                    )
                    .map((option) => option.label);
                  return (
                    <li key={contest.contestId}>
                      <strong>{contest.title}</strong>
                      <span>
                        {labels.length > 0
                          ? labels.join(", ")
                          : WS03_CONTENT.review.blank}
                      </span>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p>{WS03_CONTENT.assistance.boundary}</p>
            )}
            <div className="action-row">
              <Link
                className="button button--secondary"
                href="/vote/ballot"
                prefetch={false}
                onClick={() => journey.returnToBallot()}
              >
                {WS03_CONTENT.review.back}
              </Link>
              <button
                type="button"
                className="button button--quiet"
                onClick={() => journey.cancel()}
              >
                {WS03_CONTENT.review.cancel}
              </button>
            </div>
          </section>

          <div className="consequential-block">
            <h2>{WS03_CONTENT.review.consequential}</h2>
            <p>{WS03_CONTENT.review.consequentialBody}</p>
            <p>{WS03_CONTENT.review.exclusive}</p>

            <div className="consequential-choice">
              <div>
                <button
                  type="button"
                  className="button button--secondary"
                  disabled={journey.busy}
                  onClick={() => void journey.attemptLocalCheck()}
                >
                  {WS03_CONTENT.review.localCheckAction}
                </button>{" "}
                <CapabilityBadge status={localCheck.status} />
              </div>
              <p>{WS03_CONTENT.review.localCheckExplanation}</p>
            </div>

            <div className="consequential-choice">
              <div>
                <button
                  type="button"
                  className="button button--secondary"
                  disabled={journey.busy || !canSubmit}
                  onClick={() =>
                    void journey.attemptSubmission(
                      "public_evidentiary_challenge",
                    )
                  }
                >
                  {WS03_CONTENT.review.publicChallengeAction}
                </button>{" "}
                <CapabilityBadge status={publicChallenge.status} />
              </div>
              <p>{WS03_CONTENT.review.publicChallengeExplanation}</p>
            </div>

            <div className="consequential-choice">
              <div>
                <button
                  type="button"
                  className="button button--primary"
                  disabled={journey.busy || !canSubmit}
                  onClick={() => void journey.attemptSubmission("final_cast")}
                >
                  {WS03_CONTENT.review.castAction}
                </button>{" "}
                <CapabilityBadge status={cast.status} />
              </div>
              <p>
                Die endgültige Abgabe ist nicht umkehrbar. Sie erfordert eine
                freigegebene kryptografische Laufzeit ({crypto.status}) und
                einen freigegebenen Übermittlungsvertrag ({cast.status}).
              </p>
            </div>
          </div>
        </>
      )}

      {journey.refusal ? (
        <RefusalPanel
          title="Vorgang nicht ausgeführt"
          refusal={journey.refusal}
        />
      ) : null}

      <AssistancePanel />
      <GovernedFallback />
    </>
  );
}
