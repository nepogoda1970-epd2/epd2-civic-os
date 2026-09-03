"use client";

import { useId, useState } from "react";

import { WS03_CONTENT } from "../content/de";
import {
  SUPPORT_OPERATOR_FORBIDDEN_CAPABILITIES,
  mayChangeBallotSelections,
  mayViewBallotSelections,
} from "../policies/supportRole";

/**
 * Accessibility assistance.
 *
 * The panel explains the page.  It has no access to ballot state: the component
 * is not given selections as a prop and there is no path from here to them.
 * The two policy calls below are rendered as text so the boundary is visible to
 * the person being helped as well as to a reviewer, and so a test can assert
 * that the operator's answer is `false` on the page itself.
 */
export function AssistancePanel() {
  const [open, setOpen] = useState(false);
  const bodyId = useId();
  return (
    <section className="card" data-assistance>
      <h2 className="card-title">{WS03_CONTENT.assistance.title}</h2>
      <button
        type="button"
        className="button button--secondary"
        aria-expanded={open}
        aria-controls={bodyId}
        onClick={() => setOpen((value) => !value)}
      >
        {open
          ? WS03_CONTENT.assistance.modeOn
          : WS03_CONTENT.assistance.modeOff}
      </button>
      <div id={bodyId} hidden={!open}>
        <p>{WS03_CONTENT.assistance.boundary}</p>
        <p>{WS03_CONTENT.assistance.keyboard}</p>
        <p
          className="informational"
          data-operator-may-view-selections={String(
            mayViewBallotSelections("accessibility_support_operator"),
          )}
          data-operator-may-change-selections={String(
            mayChangeBallotSelections("accessibility_support_operator"),
          )}
        >
          Eine unterstützende Person hat auf die Auswahl keinen Zugriff:{" "}
          {SUPPORT_OPERATOR_FORBIDDEN_CAPABILITIES.length} Vorgänge sind für
          diese Rolle ausgeschlossen.
        </p>
      </div>
    </section>
  );
}
