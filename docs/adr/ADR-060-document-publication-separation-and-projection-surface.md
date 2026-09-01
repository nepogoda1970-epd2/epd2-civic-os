# ADR-060: Publication separated from approval, and the single projection surface

## Status

`proposed`

## Date

2026-07-28

## Context

`FIR-INV-015` forbids false production, legal-validity and security
claims. PACK-04 owns the public transparency register and already
registers `PUBLICATION_NOT_ALLOWED` and `DISCLOSURE_POLICY_VIOLATION`.
PACK-12 will own controlled export and DLP.

## Problem

1. A single "release" act would mean whoever can approve can publish -
   which is precisely the control a governed register exists to provide.
2. A projection that could be constructed claiming authority would let a
   derived view be mistaken for the record.
3. A revoked publication that simply disappeared from the public view
   would be a silent retraction of something the public was already told.
4. Every export path added independently is another surface PACK-12 must
   later find and govern.
5. Publishing a `restricted` document to a public audience would be a
   reclassification nobody recorded.

## Decision

**1. Approval and publication are two acts, two authorities, two records
and two transitions.** `ApprovalRecord` is issued by `document_approver`;
`PublicationAuthorization` by `publication_officer`; `publish_version`
requires both, and `assert_publishable` checks approval _before_
authorization because "authorized to publish something never approved" is
the error worth naming first.

**2. A publication authorization requires a
`disclosure_obligation_reference`.** This service does not decide what
must or may be published - that is a legal question - and refuses to
proceed without the caller naming the obligation or decision it acts
under. A publication with no stated basis is one nobody can later be held
to.

**3. `is_authoritative` is a read-only property returning `False`, not a
field.** A field could be constructed `True`; a property cannot, and the
distinction survives `dataclasses.replace`, deserialisation and every
future field somebody adds (Problem 2).

**4. A revoked publication becomes a tombstone.** It states that a
publication occurred and that it was revoked, when, and under which reason
code - and carries no rendition and no citation. `REVOKED` is therefore in
`PUBLICLY_REPRESENTABLE_STATES` on purpose (Problem 3).

**5. The public and restricted projections are separate types, not one
type with a flag.** A shared type with a `public` flag would mean one
wrong flag exposes every restricted field at once; two types mean the
public surface can only be handed something whose every field was chosen
for it.

**6. Emission is one chokepoint.** Every projection and every event
payload runs `domain.assert_emission_safe` - content, identity and voting
linkage, in that order - over its own output _before_ being returned, so a
leaking payload never comes into existence. PACK-12 can attach DLP at one
place rather than auditing every call site (Problem 4).

**7. No projection carries content, at any sensitivity.** The restricted
projection is richer than the public one in _metadata_ and identical to it
in carrying nothing of what the document says. Reading content is
`application.read_document_content`: authority-checked, access-profile-checked,
integrity-checked, and audited.

**8. Publication does not reclassify.** A `restricted` version cannot be
projected publicly even under a public publication authorization (Problem
5).

**9. Review findings travel as counts, never as text.** A reviewer's
finding on a membership appeal is exactly the internal deliberation
`FIR-MEM-001` says the applicant must not see. `open_blocking_review_count`
answers "is this contested?" without answering "with what?".

**10. `title_reference`, never `title`.** A document's title is content:
"Beschwerde gegen den Aufnahmebescheid von …" names a person as reliably
as a `full_name` field would.

## Consequences

Only four of the twenty-five event types are publicly projectable, and the
allow-list is closed rather than a deny-list - a deny-list would admit
every event type somebody adds later, and the default for a governance
stream must be "not public".

`PublicationRendition.citation_reference` closes ADR-053's fourth
interface requirement: a public view cites
`epd2-doc:<document>:v<n>:r<rendition>` and gets existence, audience and
media type, never content.

## Alternatives considered

**One release act with a two-person check inside it.** Rejected: the check
would be internal to one command and therefore removable by one edit.

**Remove revoked publications from the public projection.** Rejected: see
Problem 3.

**Let the restricted projection carry finding text for authorized
readers.** Rejected: it would have to be re-audited every time a new
reader class was added.

## Security impact

The single emission chokepoint is what makes the privacy sweep in
`tests/test_privacy_boundary.py` meaningful: it can walk every payload a
full lifecycle produces, because there is only one way for a payload to be
produced.
