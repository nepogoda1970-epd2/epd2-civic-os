# Account Service

Owns `Account` (canon section 7.2; ownership matrix section 22). No other
service reads or writes this service's storage directly (INV-03).

`Account` holds no personal data — only technical account state
(`email_status`, `mfa_status`, `account_status`, `locale`,
`terms_version`, `consent_status`). It never stores an email address,
name, or any identity attribute; that is `IdentityRecord`'s concern
(Identity Service), deliberately separate (INV-01).

## Status transitions

See `domain.py`'s `ALLOWED_TRANSITIONS`. `closed` is terminal — no
transition out of it is ever allowed. An unknown status is always
rejected fail-closed (CT-00-02); a transition not in the allowed table is
always rejected (CT-00-03). Which transitions beyond `create` are
business-approved (e.g. auto-activation vs. manual review) is flagged as
open in `docs/review/OPEN_QUESTIONS.md` — this service takes the most
conservative reading of canon section 7.2's status list.

## Events

Emits canonical events only where canon section 20.1 defines one:
`account.created`, `account.restricted`, `account.suspended`,
`account.closed`. Transitions with no canonical event name (e.g.
`pending → active`) do not emit an event — see ADR-002.
