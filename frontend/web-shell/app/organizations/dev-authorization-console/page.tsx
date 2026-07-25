"use client";

import Link from "next/link";
import { useId, useState } from "react";

import { Bilingual } from "../Bilingual";
import { checkSampleRegionalScopeAccess } from "../authorization";
import { SAMPLE_ACCESS_GRANTS, SAMPLE_ORGANIZATIONS } from "../data";
import { ACCESS_MODE_LABELS, LABELS } from "../labels";
import type { AuthorizationCheckResult } from "../authorization";

const SUBJECT_REFERENCES = Array.from(
  new Set(SAMPLE_ACCESS_GRANTS.map((grant) => grant.subject_reference)),
).concat("30000000-0000-0000-0000-000000000099");

const ACTION_CODES = Array.from(
  new Set(SAMPLE_ACCESS_GRANTS.map((grant) => grant.action_code)),
).concat("administer_organization");

/**
 * Development-only authorization test console.
 *
 * This page is a demonstration/testing tool for canon 19e.12's default-deny
 * regional scope access model. It is NOT connected to any backend, issues
 * no network request, and its result is NOT a real authorization decision —
 * see checkSampleRegionalScopeAccess's own doc comment. It exists so this
 * vertical slice can show the default-deny access-mode shape end to end
 * without a running organization-service HTTP API (none exists in this
 * repository yet, see contracts/openapi/pack-08.yaml's scope note).
 */
export default function DevAuthorizationConsolePage() {
  const subjectId = useId();
  const scopeId = useId();
  const actionId = useId();
  const asOfId = useId();

  const [subjectReference, setSubjectReference] = useState(
    SUBJECT_REFERENCES[0],
  );
  const [scopeReference, setScopeReference] = useState(
    SAMPLE_ORGANIZATIONS[0].organization_id,
  );
  const [actionCode, setActionCode] = useState(ACTION_CODES[0]);
  const [asOf, setAsOf] = useState("2026-07-25");
  const [result, setResult] = useState<AuthorizationCheckResult | null>(null);

  function runCheck() {
    setResult(
      checkSampleRegionalScopeAccess({
        subjectReference,
        scopeType: "organization_scope",
        scopeReference,
        actionCode,
        asOf: new Date(asOf).toISOString(),
      }),
    );
  }

  return (
    <main lang="de">
      <p>
        <Link href="/organizations">
          &larr; <Bilingual pair={LABELS.backToList} />
        </Link>
      </p>

      <h1>
        <Bilingual pair={LABELS.devConsoleHeading} />
      </h1>

      <p role="alert" className="dev-banner">
        <Bilingual pair={LABELS.devConsoleBanner} />
      </p>

      <p>
        <Bilingual pair={LABELS.devConsoleIntro} />
      </p>

      <div role="group" aria-label={LABELS.devConsoleHeading.de}>
        <p>
          <label htmlFor={subjectId}>
            <Bilingual pair={LABELS.subjectLabel} />
          </label>
          <br />
          <select
            id={subjectId}
            value={subjectReference}
            onChange={(event) => setSubjectReference(event.target.value)}
          >
            {SUBJECT_REFERENCES.map((reference) => (
              <option key={reference} value={reference}>
                {reference}
              </option>
            ))}
          </select>
        </p>

        <p>
          <label htmlFor={scopeId}>
            <Bilingual pair={LABELS.scopeLabel} />
          </label>
          <br />
          <select
            id={scopeId}
            value={scopeReference}
            onChange={(event) => setScopeReference(event.target.value)}
          >
            {SAMPLE_ORGANIZATIONS.map((organization) => (
              <option
                key={organization.organization_id}
                value={organization.organization_id}
              >
                {organization.name}
              </option>
            ))}
          </select>
        </p>

        <p>
          <label htmlFor={actionId}>
            <Bilingual pair={LABELS.actionLabel} />
          </label>
          <br />
          <select
            id={actionId}
            value={actionCode}
            onChange={(event) => setActionCode(event.target.value)}
          >
            {ACTION_CODES.map((action) => (
              <option key={action} value={action}>
                {action}
              </option>
            ))}
          </select>
        </p>

        <p>
          <label htmlFor={asOfId}>
            <Bilingual pair={LABELS.asOfLabel} />
          </label>
          <br />
          <input
            id={asOfId}
            type="date"
            value={asOf}
            onChange={(event) => setAsOf(event.target.value)}
          />
        </p>

        <p>
          <button type="button" onClick={runCheck}>
            <Bilingual pair={LABELS.runCheck} />
          </button>
        </p>
      </div>

      <div aria-live="polite">
        {result && (
          <dl>
            <dt>
              <Bilingual
                pair={
                  result.allowed ? LABELS.resultAllowed : LABELS.resultDenied
                }
              />
            </dt>
            <dd>
              <Bilingual pair={LABELS.reasonCode} />:{" "}
              <code>{result.reasonCode}</code>
            </dd>
            {result.mode && (
              <>
                <dt>
                  <Bilingual pair={LABELS.accessMode} />
                </dt>
                <dd>
                  <Bilingual pair={ACCESS_MODE_LABELS[result.mode]} />
                </dd>
              </>
            )}
          </dl>
        )}
      </div>
    </main>
  );
}
