# ADR-080 — Account, person record and membership are separate identities

**Status:** proposed
**Round:** PACK-14 — Identity, Authentication & Account Security (specification and ADR only)
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`

**NO CODE. NOT IMPLEMENTED. NOT A CANDIDATE. NOT A PASS. NOT PRODUCTION
READY. NOT LEGALLY ACTIVATED.**

## Context

"The user" is four different things in this system and conflating any two
of them destroys a guarantee. An account is a way to log in. A person
record is the result of identity proofing. A membership is a governed
legal relationship with the party. A communication persona is how someone
appears to other members. They have different lifecycles, different owners,
different retention rules and different failure modes.

Canon already separates them — `Account` (7.2, Account Service),
`IdentityRecord` (7.3/19d.2, Identity Verification Service), `Membership`
(8.3) and `MembershipApplication` (19d.9, with its mandatory two-stage
human decision). PACK-14 must not quietly re-merge them at the
authentication layer, which is exactly where such merges happen.

## Decision

Five identity layers are normatively distinct, each with its own
identifier space, owner and lifecycle:

| Layer                 | Identifier                       | What it is                                                      | What it is **not**                                        |
| --------------------- | -------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------- |
| Account identity      | `account_id`                     | A technical login and session subject                           | A person, a member, a public number, a voter              |
| Protected person      | `person_record_id`               | The subject of identity proofing, where required                | A general integration key; not required for every account |
| Membership identity   | `membership_id`, `member_number` | The governed relationship and its visible organizational number | A login identifier; not a correlation key                 |
| Applicant identity    | application-scoped reference     | Someone who has applied and has not been admitted               | A membership; never auto-promoted                         |
| Communication persona | `communication_persona_id`       | How a member appears in permitted internal communication        | An authentication subject or a membership decision input  |

Binding rules:

- An account **may exist with no person record and no membership.**
  Registration does not create a member.
- An applicant **never** receives membership identity automatically.
  Canon 19d.9's two-stage process is unchanged and PACK-14 adds no path
  around it.
- `member_number` may be shown to a member and printed on organizational
  documents. It is **not** a login identifier and **not** a cross-domain
  key.
- The communication persona is never an authentication subject and never
  an input to a membership decision.
- Voting credentials are a separate identity space entirely, owned by
  PACK-15/16 and untouched here (ADR-088).

## Consequences

Account closure and membership termination are different operations with
different authorities, and neither implies the other. A person may hold an
account, lose membership and keep the account; a member may be admitted
through an assisted channel and hold no account at all. The specification
must therefore describe every combination rather than assume the common
one — which it does, in the identity separation matrix.

Duplicate accounts become a governed review with an explicit decision and
a reason code, because the automatic merge key does not exist (ADR-079).
That is slower and it is correct: merging two accounts by matching email
and name is precisely how one person's records are silently attached to
another's.
