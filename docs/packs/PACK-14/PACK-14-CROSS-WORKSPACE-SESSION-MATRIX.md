# PACK-14 — Cross-Workspace Session Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Derived from `frontend/web-shell/foundation/workspaces.ts`, in which every
workspace already declares `sessionSharing: forbidden`. PACK-14 issues
sessions that honour those declarations. Origins are the documented
placeholders and are not deployment decisions.

## 0. Authentication bootstrap across origins — decided

**This is not SSO, and no document in this pack describes it as a shared
application session.** There is no shared session. There is a per-workspace
authentication ceremony that may reuse a completed identity verification
without reusing a session (OD-P14-06).

| Step | Rule                                                                                                                                            |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | **Each protected workspace starts its own authentication ceremony.** Nothing is inherited by being on a sibling origin                          |
| 2    | `identity-service` returns a **single-use, short-lived, audience-bound authorization response** naming the workspace and the assurance achieved |
| 3    | **The workspace creates its own origin-local session** from that response; the response is spent at that moment                                 |
| 4    | **No parent-domain cookie is ever issued**                                                                                                      |
| 5    | **No token is reusable across origins** — wrong audience is refused with `CROSS_WORKSPACE_HANDOFF_INVALID`                                      |
| 6    | **No shared browser-storage identity** — not localStorage, sessionStorage, IndexedDB, cache or an analytics identifier                          |
| 7    | **Crossing into a higher-risk boundary requires new authentication or step-up**, never a token exchange                                         |

Why the distinction is load-bearing: under SSO one credential compromise
yields sessions everywhere and one stolen cookie crosses every boundary.
Here each workspace holds only what it minted for itself, revocation is
scoped, and the authorization response is worthless the moment after it is
used.

## 1. Workspaces

| WS    | Name                                 | Origin placeholder                 | Sensitivity                                       | Authentication bootstrap  | Session cookies   | Browser storage as identity | Crossing into it from a lower tier |
| ----- | ------------------------------------ | ---------------------------------- | ------------------------------------------------- | ------------------------- | ----------------- | --------------------------- | ---------------------------------- |
| WS-01 | Public Website                       | `https://www.epd.example`          | PUBLIC_APPROVED                                   | none required             | none for identity | prohibited                  | n/a                                |
| WS-02 | Member Application                   | `https://app.epd.example`          | INTERNAL; CONFIDENTIAL_CASE_SCOPED                | full                      | own origin only   | prohibited                  | authenticate                       |
| WS-03 | **Voting Client**                    | `https://vote.epd.example`         | VOTING_SCOPED; NO_DIRECT_IDENTITY                 | **none — handoff only**   | **none**          | **prohibited entirely**     | one-time handoff (§2)              |
| WS-04 | Mandate Holder Workspace             | `https://represent.epd.example`    | MANDATE_INTERNAL; CASE_CONFIDENTIAL               | full                      | own origin only   | prohibited                  | reauthenticate                     |
| WS-05 | Citizen Office Portal                | `https://office.epd.example`       | CASE_CONFIDENTIAL; SPECIAL_CATEGORY_POSSIBLE      | full                      | own origin only   | prohibited                  | reauthenticate                     |
| WS-06 | Institutional Administration         | `https://admin.epd.example`        | RESTRICTED_ADMIN; SECURITY_SENSITIVE              | full + PACK-12 grant      | own origin only   | prohibited                  | reauthenticate at `high`           |
| WS-07 | Compliance & Legal Workspace         | `https://legal.epd.example`        | LEGAL_PRIVILEGED; EVIDENCE_RESTRICTED             | full + PACK-12 grant      | own origin only   | prohibited                  | reauthenticate at `high`           |
| WS-08 | Finance Workspace                    | `https://finance.epd.example`      | FINANCIAL_CONFIDENTIAL                            | full + PACK-12 grant      | own origin only   | prohibited                  | reauthenticate at `high`           |
| WS-09 | Independent Oversight & Verification | `https://verify.epd.example`       | OVERSIGHT_RESTRICTED; PUBLIC_VERIFICATION         | full + independence check | own origin only   | prohibited                  | reauthenticate at `high`           |
| WS-10 | Transparency Publication Portal      | `https://transparency.epd.example` | PUBLIC_APPROVED; AGGREGATED_DISCLOSURE_CONTROLLED | none required             | none for identity | prohibited                  | n/a                                |

**No parent-domain cookie is issued for any workspace.** No token is
reusable across origins. No shared analytics identity exists. No
localStorage, sessionStorage or IndexedDB entry is an identity bridge in
any workspace.

## 2. WS-03 — the Voting Client boundary

Prohibited, structurally and completely: shared cookies, local cookies,
localStorage, sessionStorage, IndexedDB, cache storage, service worker,
shared identity session, analytics, fingerprinting, shared telemetry,
persistent member identifier, general account ID, membership number,
reusable bearer token, reverse identity bridge.

Permitted: **one** one-time, purpose-scoped, short-lived,
audience-restricted handoff artifact carrying **no identity**.

| Handoff property    | Requirement                                             | Violation reason code             |
| ------------------- | ------------------------------------------------------- | --------------------------------- |
| Single use          | A second presentation is refused                        | `VOTING_HANDOFF_ALREADY_USED`     |
| Purpose-scoped      | One voting context only                                 | `CROSS_WORKSPACE_HANDOFF_INVALID` |
| Short-lived         | Expiry checked at redemption                            | `CROSS_WORKSPACE_HANDOFF_INVALID` |
| Audience-restricted | WS-03 origin only                                       | `CROSS_WORKSPACE_HANDOFF_INVALID` |
| Carries no identity | No account, person, membership, persona or contact data | —                                 |
| Not reversible      | Voting-side data cannot resolve back to the account     | —                                 |

**PACK-14 defines this boundary and does not define the voting credential
protocol** (ADR-088). Eligibility, ballots, verification and tally are
PACK-15/16.

## 3. Mobile App channel

The Mobile App is not a workspace. Its catalogue scope is WS-02 plus
explicitly user-facing WS-05 request status. For voting it may only open
WS-03 **in the system browser** using the declared one-time handoff. An
embedded WebView, a transferred member session, a persistent member
identifier and shared cookies, storage or analytics remain prohibited.
