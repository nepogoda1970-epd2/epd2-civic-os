# FRONT-00 Telemetry Policy

No analytics platform is connected. `validateTelemetryEvent()` fails closed when
analytics is disabled and rejects user/member/global identifiers, ballots,
credentials, messages, documents and free-form field content.

Permitted future observability is workspace-local, minimal and technical. It may
not fingerprint a browser, correlate origins, profile political interests or
create a bridge between WS-02 and WS-03. WS-03 permits no analytics or telemetry.

Mobile analytics may not infer political preferences. Crash logs may not contain
PII, tokens, ballot data, or legal content. Push providers are not trusted
storage; payloads are neutral, minimal routing/status data only and never contain
political, voting, legal-case, or sensitive membership content.
