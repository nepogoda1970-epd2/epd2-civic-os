# FRONT-00 Implementation

The existing `frontend/web-shell` Next.js 15 / React 19 / TypeScript stack is used.
No dependency was added. `app/globals.css` carries normalized tokens derived from
the visual baseline. `components/foundation.tsx` provides server-compatible
primitives; `DialogExample.tsx` is the only client component.

`foundation/workspaces.ts`, `routes.ts`, `storage-policy.ts` and
`telemetry-policy.ts` contain policy-oriented typed registries. Example routes
under `/foundation/examples/[kind]` are conspicuously non-production fixtures.
They do not fetch, authenticate, save, submit or claim legal effect.

`foundation/mobile-application-profile.ts` adds the inactive EPD² Mobile App as
a client channel only. It declares capability, handoff, push, security, offline,
delivery-sequencing, and source/runtime-sharing policy. It contains no mobile
framework, API, device registration, push delivery, deep link, authentication,
or voting implementation.
