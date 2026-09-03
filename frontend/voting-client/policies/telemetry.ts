/**
 * Telemetry policy for WS-03: there is none.
 *
 * FRONT-03 carried a permitted-field allowlist for the Member Workspace.  The
 * Voting Client has no allowlist, because it emits no measurement event at
 * all.  `telemetryPermitted` exists so that a future attempt to add one has to
 * change a function a gate reads rather than simply adding a call site.
 */

export const WS03_TELEMETRY_EVENTS_PERMITTED = false as const;
export const WS03_TELEMETRY_ALLOWED_FIELDS = Object.freeze([] as const);

export function telemetryPermitted(): false {
  return false;
}

export function validateTelemetryEvent(event: unknown): false {
  void event;
  return false;
}

/**
 * Error reports are permitted to leave the browser only if they carry no
 * identity, no ballot material and no correlation handle.  No accepted error
 * reporting contract exists for WS-03, so the answer today is the same as for
 * telemetry: nothing is sent.
 */
export const WS03_ERROR_REPORTING = Object.freeze({
  enabled: false,
  carriesIdentity: false,
  carriesBallotMaterial: false,
  carriesCorrelationHandle: false,
} as const);
