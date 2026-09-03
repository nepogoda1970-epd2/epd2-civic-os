"use client";

import Link from "next/link";

import { useEffect } from "react";

import { WS03_CONTENT } from "../content/de";
import {
  blankContestIds,
  contestValidity,
  readyForReview,
  selectionFor,
} from "../domain/ballot";
import { capability } from "../domain/capabilities";
import {
  CapabilityBadge,
  ErrorSummary,
  GovernedFallback,
  JourneyStatus,
  Notice,
  RefusalPanel,
} from "./primitives";
import { AssistancePanel } from "./assistance";
import { useJourney } from "./JourneyProvider";

/**
 * PAGE-017 — Stimmzettel.
 *
 * Selections are held in the journey provider's memory and nowhere else.  No
 * option identifier reaches the URL, the title, storage or a report, and the
 * page shows no count, distribution, turnout or progress of any kind.
 */
export function BallotSurface() {
  const journey = useJourney();

  useEffect(() => {
    void journey.openBallot();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const record = capability("ballot_style");
  const style = journey.style;
  const draft = journey.draft;

  const overLimit =
    style && draft
      ? style.contests
          .filter(
            (contest) =>
              contestValidity(style, draft, contest.contestId).kind ===
              "over_limit",
          )
          .map((contest) => ({
            id: `contest-${contest.contestId}`,
            message: `${contest.title}: zu viele Auswahlmöglichkeiten markiert.`,
          }))
      : [];

  return (
    <>
      <div className="page-header">
        <h1>{WS03_CONTENT.ballot.title}</h1>
        <p>{WS03_CONTENT.ballot.lead}</p>
      </div>

      <p>
        <CapabilityBadge status={record.status} />{" "}
        <span className="informational">Stimmzettel</span>
      </p>

      <JourneyStatus state={journey.state} />

      {journey.busy ? (
        <p role="status" aria-live="polite">
          {WS03_CONTENT.states.loading}
        </p>
      ) : null}

      {journey.refusal ? (
        <RefusalPanel
          title={WS03_CONTENT.ballot.unavailableTitle}
          refusal={journey.refusal}
        />
      ) : null}

      {journey.election ? (
        <section className="card">
          <h2 className="card-title">{journey.election.title}</h2>
          <dl className="metadata-list">
            <div>
              <dt>Kontext</dt>
              <dd>{journey.election.electionContextReference}</dd>
            </div>
            <div>
              <dt>Aktivierung</dt>
              <dd>{journey.election.activationStatus}</dd>
            </div>
          </dl>
        </section>
      ) : null}

      {style && draft ? (
        <>
          <ErrorSummary
            title="Bitte prüfen Sie Ihre Auswahl"
            items={overLimit}
          />
          <Notice kind="information" title="Ihre Auswahl">
            <p>{WS03_CONTENT.ballot.selectionKept}</p>
            <p>{WS03_CONTENT.ballot.blankAllowed}</p>
          </Notice>

          {style.contests.map((contest) => {
            const selection = selectionFor(draft, contest.contestId);
            const single = contest.selectionLimit === 1;
            return (
              <fieldset
                key={contest.contestId}
                id={`contest-${contest.contestId}`}
              >
                <legend>{contest.title}</legend>
                <p className="hint">{contest.instruction}</p>
                <p className="hint" aria-live="polite">
                  {WS03_CONTENT.ballot.selectedCount
                    .replace("{n}", String(selection.optionIds.length))
                    .replace("{limit}", String(contest.selectionLimit))}
                </p>
                {contest.options.map((option) => {
                  const checked = selection.optionIds.includes(option.optionId);
                  const inputId = `${contest.contestId}-${option.optionId}`;
                  return (
                    <div className="ballot-option" key={option.optionId}>
                      <input
                        id={inputId}
                        type={single ? "radio" : "checkbox"}
                        name={contest.contestId}
                        value={option.optionId}
                        checked={checked}
                        aria-describedby={
                          option.description
                            ? `${inputId}-description`
                            : undefined
                        }
                        onChange={() =>
                          journey.toggleOption(
                            contest.contestId,
                            option.optionId,
                          )
                        }
                      />
                      <span>
                        <label
                          htmlFor={inputId}
                          className={
                            checked ? "ballot-option__selected" : undefined
                          }
                        >
                          {option.label}
                          <span className="visually-hidden">
                            {checked ? " — ausgewählt" : " — nicht ausgewählt"}
                          </span>
                        </label>
                        {option.description ? (
                          <p id={`${inputId}-description`}>
                            {option.description}
                          </p>
                        ) : null}
                      </span>
                    </div>
                  );
                })}
                <p>
                  <button
                    type="button"
                    className="button button--quiet"
                    onClick={() => journey.clearContest(contest.contestId)}
                  >
                    {WS03_CONTENT.ballot.clearContest}
                  </button>
                </p>
              </fieldset>
            );
          })}

          <p
            className="informational"
            data-blank-contests={blankContestIds(style, draft).length}
          >
            {WS03_CONTENT.ballot.blankAllowed}
          </p>

          <div className="action-row">
            <Link
              className="button button--primary"
              href="/vote/review"
              prefetch={false}
              aria-disabled={!readyForReview(style, draft)}
              onClick={(event) => {
                if (!readyForReview(style, draft)) event.preventDefault();
              }}
            >
              {WS03_CONTENT.ballot.toReview}
            </Link>
          </div>
        </>
      ) : null}

      <AssistancePanel />
      <GovernedFallback />
    </>
  );
}
