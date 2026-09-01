"""External identity providers - an adapter boundary, and no provider.

**No provider is selected by this round.** What exists is the set of
checks any adapter must satisfy before an assertion is believed: issuer,
audience, expiration, issued-at, nonce, replay, signature (through a
port), and attribute minimization.

The rule that matters most is the one about the subject claim. A
provider-issued stable subject identifier is exactly the shape of a
global user ID, and the temptation to store it as the account's key is
the single easiest way to lose `FIR-INV-001`. So:

- `ProviderSubjectReference` holds a **digest**, never the raw claim;
- it is linked to an account only through an explicit, user-initiated,
  step-up-protected link (see `linking.py`);
- an unlinked subject produces `EXTERNAL_SUBJECT_NOT_LINKED` and
  **never** an implicitly created or matched account.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    ExternalAssertionInvalidError,
    ExternalAssertionReplayedError,
    ExternalProviderUnavailableError,
    ExternalSubjectNotLinkedError,
    GlobalIdentifierRefusedError,
    IdentityAssertionExpiredError,
)
from epd2_identity_service.identifiers import require_timezone

#: How far a provider's `issued_at` may be in the future before it is
#: refused. Clock skew is real and small; an assertion minted ten minutes
#: ahead is not skew.
MAXIMUM_CLOCK_SKEW = timedelta(minutes=2)


@dataclass(frozen=True, slots=True)
class ProviderSubjectReference:
    """A provider's subject claim, as this system is willing to hold it.

    The raw claim is hashed with the provider's issuer so the same person
    at two providers produces two unrelated references, and so a database
    read yields nothing that can be presented to the provider or joined
    across domains.
    """

    issuer: str
    subject_digest: str

    def __post_init__(self) -> None:
        if not self.issuer:
            raise ExternalAssertionInvalidError("a subject reference names its issuer")
        if len(self.subject_digest) != 64:
            raise ValueError("subject_digest must be a 64-character hex digest")


def derive_subject_reference(*, issuer: str, raw_subject: str) -> ProviderSubjectReference:
    if not raw_subject:
        raise ExternalAssertionInvalidError("the assertion carries no subject claim")
    digest = hashlib.sha256(f"{issuer}\x1f{raw_subject}".encode()).hexdigest()
    return ProviderSubjectReference(issuer=issuer, subject_digest=digest)


def refuse_subject_as_account_key(reference: ProviderSubjectReference) -> None:
    """ADR-079 §3, as a call site. Always raises.

    Called by anything that is about to use a provider subject as an
    account's primary key, a lookup key or a cross-domain join key.
    """
    raise GlobalIdentifierRefusedError(
        f"the subject claim from {reference.issuer!r} is never an account key, a lookup key "
        "or a cross-domain join key"
    )


@dataclass(frozen=True, slots=True)
class ExternalIdentityProvider:
    """A registered adapter.

    `permitted_attributes` is the minimization commitment as data: an
    adapter releases these attribute names and no others, and
    `validate_assertion` refuses an assertion that carries more.
    `assessed_assurance` is what **this** system's own assessment of the
    provider concluded - a provider never grants assurance above it.
    """

    provider_id: UUID
    issuer: str
    audience: str
    permitted_attributes: frozenset[str]
    assessed_assurance: AuthenticationAssuranceLevel
    assertion_lifetime: timedelta

    def __post_init__(self) -> None:
        if not self.issuer or not self.audience:
            raise ExternalAssertionInvalidError("a provider registration names issuer and audience")


@dataclass(frozen=True, slots=True)
class ExternalIdentityAssertion:
    """An assertion as received. Never stored in this shape.

    `signature` is present so the signature port can be handed it, and is
    not carried onto any record; `attributes` holds only the names and
    values an adapter released, and is discarded once the derived facts
    are taken.
    """

    assertion_id: str
    issuer: str
    audience: str
    subject: str
    nonce: str
    issued_at: datetime
    expires_at: datetime
    signature: str
    attributes: frozenset[str]

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, "issued_at")
        require_timezone(self.expires_at, "expires_at")


class AssertionSignatureVerifier(Protocol):
    """The signature port.

    No signature algorithm is implemented in this repository. A
    deployment binds this to the provider's own library or to a mature
    JOSE implementation.
    """

    def verify(self, assertion: ExternalIdentityAssertion, *, issuer: str) -> bool: ...


class UnboundAssertionSignatureVerifier:
    """The default binding: refuses.

    An unbound verifier means the deployment has registered no provider,
    which is the state this round ships in.
    """

    def verify(self, assertion: ExternalIdentityAssertion, *, issuer: str) -> bool:
        raise ExternalProviderUnavailableError(
            "no assertion signature verifier is bound; no external provider is configured"
        )


class DeterministicAssertionSignatureVerifier:
    """A **test double**. Accepts the fixture signature
    `f"{issuer}:{assertion_id}"` and nothing else."""

    def verify(self, assertion: ExternalIdentityAssertion, *, issuer: str) -> bool:
        return assertion.signature == f"{issuer}:{assertion.assertion_id}"


@dataclass(frozen=True, slots=True)
class AssertionValidationResult:
    """What survives validation: derived facts, never raw attributes."""

    subject_reference: ProviderSubjectReference
    achieved_assurance: AuthenticationAssuranceLevel
    validated_at: datetime
    released_attributes: frozenset[str]


def validate_assertion(
    assertion: ExternalIdentityAssertion,
    *,
    provider: ExternalIdentityProvider,
    expected_nonce: str,
    verifier: AssertionSignatureVerifier,
    seen_assertion_ids: frozenset[str],
    now: datetime,
) -> AssertionValidationResult:
    """The eight checks, in an order chosen so the cheapest structural
    refusals happen before the signature verification.

    Replay is checked as its own refusal rather than folded into
    "invalid": a replayed assertion is an attack and a malformed one is
    usually a bug, and an incident review needs to tell them apart.
    """
    moment = require_timezone(now, "now")
    if assertion.issuer != provider.issuer:
        raise ExternalAssertionInvalidError("the assertion issuer does not match the registration")
    if assertion.audience != provider.audience:
        raise ExternalAssertionInvalidError(
            "the assertion audience does not match the registration"
        )
    if assertion.assertion_id in seen_assertion_ids:
        raise ExternalAssertionReplayedError("this assertion has already been consumed")
    if assertion.nonce != expected_nonce:
        raise ExternalAssertionInvalidError("the assertion nonce does not match the request")
    if assertion.issued_at > moment + MAXIMUM_CLOCK_SKEW:
        raise ExternalAssertionInvalidError("the assertion is issued further ahead than clock skew")
    if moment >= assertion.expires_at:
        raise IdentityAssertionExpiredError("the assertion is outside its freshness window")
    if moment - assertion.issued_at > provider.assertion_lifetime:
        raise IdentityAssertionExpiredError(
            "the assertion is older than this provider's governed assertion lifetime"
        )
    extra = assertion.attributes - provider.permitted_attributes
    if extra:
        raise ExternalAssertionInvalidError(
            f"the assertion releases attributes this adapter does not permit: {sorted(extra)}"
        )
    if not verifier.verify(assertion, issuer=provider.issuer):
        raise ExternalAssertionInvalidError("the assertion signature did not verify")
    return AssertionValidationResult(
        subject_reference=derive_subject_reference(
            issuer=provider.issuer, raw_subject=assertion.subject
        ),
        achieved_assurance=provider.assessed_assurance,
        validated_at=moment,
        released_attributes=assertion.attributes,
    )


def resolve_linked_account(
    result: AssertionValidationResult,
    *,
    linked_account_reference: object | None,
) -> object:
    """No implicit account creation, and no implicit matching.

    An assertion for an unlinked subject is a refusal. Creating an
    account here, or matching one by an attribute the assertion happens
    to carry, is how a provider subject becomes the account key by
    accident.
    """
    if linked_account_reference is None:
        raise ExternalSubjectNotLinkedError(
            f"the subject from {result.subject_reference.issuer!r} is not linked to an account; "
            "linking is user-initiated and step-up protected"
        )
    return linked_account_reference
