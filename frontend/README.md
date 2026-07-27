# Frontend

- `web-shell` — minimal Next.js frontend skeleton for EPD² Civic OS. As of
  PACK-08 it also includes the first read-only vertical slice,
  `/organizations` (Organization & Regional Scope domain, canon 19e),
  built entirely on static sample data — see `web-shell/README.md`.

No other frontend applications exist at this stage.

## FRONT-00

The shared frontend foundation candidate lives in `web-shell/foundation`,
`web-shell/components` and `/foundation`. It preserves the EPD visual baseline,
declares ten isolated workspace contexts and provides non-production component
fixtures. See `docs/frontend/FRONT-00-SPECIFICATION.md`.
