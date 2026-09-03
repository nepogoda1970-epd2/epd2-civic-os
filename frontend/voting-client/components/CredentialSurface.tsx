"use client";

import Link from "next/link";

import { useEffect, useState } from "react";

import { WS03_CONTENT } from "../content/de";
import { capability } from "../domain/capabilities";
import { urlCarriesHandoffChannelViolation } from "../domain/handoff";
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
 * PAGE-016 — Stimmberechtigung übernehmen.
 *
 * A direct visit establishes nothing.  The surface attempts the handoff through
 * the runtime port, which is the only path that exists, and renders the refusal
 * it gets back.  Routing never creates authority here: there is no branch in
 * which arriving at this URL produces a voting context.
 */
export function CredentialSurface() {
  const journey = useJourney();
  const [channelViolation, setChannelViolation] = useState(false);

  useEffect(() => {
    // A handoff value in the query string or fragment is a channel violation.
    // It is detected and refused; it is never read, stored, echoed into the
    // title or sent anywhere. The URL is left untouched so that a reviewer can
    // still see what was attempted, and nothing is derived from it.
    setChannelViolation(
      urlCarriesHandoffChannelViolation(
        window.location.pathname +
          window.location.search +
          window.location.hash,
      ),
    );
  }, []);

  useEffect(() => {
    void journey.enter();
    // The attempt runs once per mount. It is the only entry path.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const record = capability("handoff_consumption");

  return (
    <>
      <div className="page-header">
        <h1>{WS03_CONTENT.credential.title}</h1>
        <p>{WS03_CONTENT.credential.lead}</p>
      </div>

      <p>
        <CapabilityBadge status={record.status} />{" "}
        <span className="informational">Übernahme der Stimmberechtigung</span>
      </p>

      <JourneyStatus state={journey.state} />

      {channelViolation ? (
        <Notice
          kind="danger"
          title={WS03_CONTENT.credential.channelViolationTitle}
          role="alert"
        >
          <p>{WS03_CONTENT.credential.channelViolationBody}</p>
        </Notice>
      ) : null}

      <section className="card">
        <h2 className="card-title">{WS03_CONTENT.credential.whatHappens}</h2>
        <p>{WS03_CONTENT.credential.whatHappensBody}</p>
      </section>

      {journey.busy ? (
        <p role="status" aria-live="polite">
          {WS03_CONTENT.states.loading}
        </p>
      ) : null}

      {journey.refusal ? (
        <RefusalPanel
          title={WS03_CONTENT.credential.unavailableTitle}
          refusal={journey.refusal}
        />
      ) : null}

      {!journey.busy && !journey.refusal && !journey.context ? (
        <Notice
          kind="warning"
          title={WS03_CONTENT.credential.noContextTitle}
          role="alert"
        >
          <p>{WS03_CONTENT.credential.noContextBody}</p>
        </Notice>
      ) : null}

      {journey.context ? (
        <section className="state-panel" data-voting-context-established>
          <h2>Stimmberechtigung übernommen</h2>
          <p>
            Die Übergabe wurde entgegengenommen. Es wurden keine Angaben zu
            Ihrer Person übernommen.
          </p>
          <p>
            <Link
              className="button button--primary"
              href="/vote/ballot"
              prefetch={false}
            >
              Weiter zum Stimmzettel
            </Link>
          </p>
        </section>
      ) : null}

      <AssistancePanel />
      <GovernedFallback />
    </>
  );
}
