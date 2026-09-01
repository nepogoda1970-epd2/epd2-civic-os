"""Cross-origin authentication bootstrap.

**This is not SSO, and this module refuses the word.** There is no shared
application session, no parent-domain cookie and no reusable token. What
exists is a per-workspace authentication ceremony that may reuse a
completed identity verification without reusing a session (OD-P14-06):

1. The **workspace**, not the browser, starts its own ceremony. Nothing
   is inherited by being on a sibling origin.
2. `identity-service` performs the verification and returns a
   **single-use, short-lived, audience-bound authorization response**
   naming the workspace it is for and the assurance achieved.
3. The workspace creates its **own origin-local session** from that
   response. The response is spent at that moment.

The difference from SSO is not cosmetic. Under SSO one credential
compromise yields sessions everywhere and one cookie theft crosses every
boundary. Here each workspace holds only what it minted for itself, each
revocation is scoped, and the authorization response is worthless the
moment after it is used.

The response value itself is stored **hashed**, so a database read yields
nothing presentable, and it is compared in constant time.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.configuration import IdentityConfiguration
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    BootstrapAlreadyUsedError,
    BootstrapAudienceMismatchError,
    BootstrapExpiredError,
    BootstrapInvalidError,
    BootstrapNonceMismatchError,
    BootstrapProofVerificationFailedError,
    BootstrapReplayDetectedError,
    RedirectUriNotAllowlistedError,
)
from epd2_identity_service.identifiers import (
    ScopedIdentityReference,
    require_timezone,
)
from epd2_identity_service.secret_storage import (
    HashedSecret,
    SecureRandom,
    constant_time_equals,
    hash_token,
)
from epd2_identity_service.workspaces import (
    BootstrapMode,
    WorkspaceId,
    assert_issues_identity_session,
    workspace_origin,
    workspace_policy,
)


class BootstrapProofMethod(StrEnum):
    """The proof-of-possession the workspace supplies.

    `PLAIN` is present only so a refusal can name it: PKCE's plain method
    proves nothing an interceptor cannot also produce, and
    `verify_proof` rejects it.
    """

    S256 = "s256"
    PLAIN = "plain"


@dataclass(frozen=True, slots=True)
class AuthenticationBootstrapRequest:
    """A workspace's own authorization request.

    `redirect_uri` is checked against an **exact-match** allowlist, never
    a prefix match: prefix matching is how an open redirect gets built by
    accident.
    """

    request_id: UUID
    workspace: WorkspaceId
    audience_origin: str
    redirect_uri: str
    nonce: str
    proof_challenge: str
    proof_method: BootstrapProofMethod
    created_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.created_at, "created_at")
        require_timezone(self.expires_at, "expires_at")
        if self.expires_at <= self.created_at:
            raise ValueError("a bootstrap request must expire after it was created")
        if self.audience_origin != workspace_origin(self.workspace):
            raise BootstrapAudienceMismatchError(
                f"{self.audience_origin!r} is not the declared origin of {self.workspace.value}"
            )
        if not self.nonce or not self.proof_challenge:
            raise BootstrapInvalidError("a bootstrap request carries a nonce and a proof challenge")


@dataclass(frozen=True, slots=True)
class AuthenticationBootstrapResponse:
    """The single-use, audience-bound authorization response.

    It names the workspace and the assurance achieved, and it carries a
    **scoped actor reference** rather than an account identifier - no
    account ID is exposed to a workspace beyond the permitted
    purpose-scoped reference.
    """

    response_id: UUID
    request_id: UUID
    workspace: WorkspaceId
    audience_origin: str
    actor_reference: ScopedIdentityReference
    achieved_assurance: AuthenticationAssuranceLevel
    nonce: str
    value_digest: HashedSecret
    issued_at: datetime
    expires_at: datetime
    redeemed_at: datetime | None = None

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, "issued_at")
        require_timezone(self.expires_at, "expires_at")
        if self.redeemed_at is not None:
            require_timezone(self.redeemed_at, "redeemed_at")
        if self.achieved_assurance is AuthenticationAssuranceLevel.NONE:
            raise BootstrapInvalidError(
                "an authorization response is never issued for an unauthenticated context"
            )

    def is_spent(self) -> bool:
        return self.redeemed_at is not None


@dataclass(frozen=True, slots=True)
class BootstrapRedemption:
    """The record that makes single-use enforceable.

    Kept even after the response record is disposed of, so a second
    presentation is detectable rather than merely improbable.
    """

    redemption_id: UUID
    response_id: UUID
    workspace: WorkspaceId
    redeemed_at: datetime
    value_digest: HashedSecret

    def __post_init__(self) -> None:
        require_timezone(self.redeemed_at, "redeemed_at")


def assert_redirect_allowlisted(request_uri: str, allowlist: frozenset[str]) -> None:
    """Exact match, and nothing else.

    Not `startswith`, not a wildcard host, not "same origin is close
    enough". Every one of those has produced an open redirect in a real
    system, and each of them is one character away from looking correct.
    """
    if request_uri not in allowlist:
        raise RedirectUriNotAllowlistedError(
            "the redirect URI is not on this workspace's registered allowlist"
        )


def create_bootstrap_request(
    *,
    request_id: UUID,
    workspace: WorkspaceId,
    redirect_uri: str,
    redirect_allowlist: frozenset[str],
    proof_challenge: str,
    proof_method: BootstrapProofMethod,
    created_at: datetime,
    configuration: IdentityConfiguration,
    random: SecureRandom,
) -> AuthenticationBootstrapRequest:
    """Start a ceremony for one workspace.

    WS-03 never reaches here: `assert_issues_identity_session` refuses,
    because the Voting Client's only entry is the handoff artifact, which
    carries strictly less.
    """
    policy = workspace_policy(workspace)
    if policy.bootstrap is BootstrapMode.NONE_REQUIRED:
        raise BootstrapInvalidError(f"{workspace.value} requires no authentication bootstrap")
    assert_issues_identity_session(workspace)
    assert_redirect_allowlisted(redirect_uri, redirect_allowlist)
    if proof_method is BootstrapProofMethod.PLAIN:
        raise BootstrapProofVerificationFailedError(
            "the plain proof method proves nothing an interceptor cannot reproduce"
        )
    moment = require_timezone(created_at, "created_at")
    return AuthenticationBootstrapRequest(
        request_id=request_id,
        workspace=workspace,
        audience_origin=policy.origin,
        redirect_uri=redirect_uri,
        nonce=random.token(),
        proof_challenge=proof_challenge,
        proof_method=proof_method,
        created_at=moment,
        expires_at=moment + configuration.bootstrap_lifetime,
    )


def issue_bootstrap_response(
    request: AuthenticationBootstrapRequest,
    *,
    response_id: UUID,
    actor_reference: ScopedIdentityReference,
    achieved_assurance: AuthenticationAssuranceLevel,
    issued_at: datetime,
    lifetime: timedelta,
    random: SecureRandom,
) -> tuple[AuthenticationBootstrapResponse, str]:
    """Authorize a request; return the record and the value **once**.

    The plaintext value is a separate return rather than a field, so no
    persistence path can store it: only its digest is ever written.
    """
    moment = require_timezone(issued_at, "issued_at")
    if moment >= request.expires_at:
        raise BootstrapExpiredError("the bootstrap request has expired")
    value = random.token()
    response = AuthenticationBootstrapResponse(
        response_id=response_id,
        request_id=request.request_id,
        workspace=request.workspace,
        audience_origin=request.audience_origin,
        actor_reference=actor_reference,
        achieved_assurance=achieved_assurance,
        nonce=request.nonce,
        value_digest=hash_token(value),
        issued_at=moment,
        expires_at=moment + lifetime,
    )
    return response, value


def verify_proof(
    request: AuthenticationBootstrapRequest, *, proof_verifier: str, digest_of_verifier: str
) -> None:
    """Verify the PKCE-equivalent proof.

    The digest is computed by the caller through the same hashing helper
    the challenge was built with, so this module compares two strings in
    constant time and invents no primitive of its own.
    """
    if request.proof_method is not BootstrapProofMethod.S256:
        raise BootstrapProofVerificationFailedError("only the S256 proof method is accepted")
    if not proof_verifier:
        raise BootstrapProofVerificationFailedError("no proof verifier was presented")
    if not constant_time_equals(digest_of_verifier, request.proof_challenge):
        raise BootstrapProofVerificationFailedError("the proof of possession did not verify")


def redeem_bootstrap_response(
    response: AuthenticationBootstrapResponse | None,
    *,
    presented_value: str,
    presenting_workspace: WorkspaceId,
    presenting_origin: str,
    presented_nonce: str,
    redemption_id: UUID,
    now: datetime,
    prior_redemption: BootstrapRedemption | None = None,
) -> tuple[AuthenticationBootstrapResponse, BootstrapRedemption]:
    """Redeem exactly once, for exactly one audience.

    Six refusals, each with its own code, in the order that gives the
    caller the most useful answer: unknown, replayed, already spent,
    expired, wrong audience, wrong nonce. The audience check comes before
    the nonce check so a token presented to the wrong origin is reported
    as an audience mismatch rather than as a bad nonce - the two point at
    very different bugs.
    """
    if response is None:
        raise BootstrapInvalidError("no authorization response matches this value")
    if prior_redemption is not None:
        raise BootstrapReplayDetectedError("this authorization response has already been redeemed")
    if response.is_spent():
        raise BootstrapAlreadyUsedError("this authorization response was already redeemed")
    if require_timezone(now, "now") >= response.expires_at:
        raise BootstrapExpiredError("the authorization response has expired")
    if presenting_workspace is not response.workspace or presenting_origin != (
        response.audience_origin
    ):
        raise BootstrapAudienceMismatchError(
            f"this authorization response is for {response.workspace.value} "
            f"({response.audience_origin}), not {presenting_workspace.value}"
        )
    if not constant_time_equals(presented_nonce, response.nonce):
        raise BootstrapNonceMismatchError("the response nonce does not match the request")
    if not response.value_digest.matches(presented_value):
        raise BootstrapInvalidError("the presented value does not match this response")
    moment = require_timezone(now, "now")
    return (
        replace(response, redeemed_at=moment),
        BootstrapRedemption(
            redemption_id=redemption_id,
            response_id=response.response_id,
            workspace=response.workspace,
            redeemed_at=moment,
            value_digest=response.value_digest,
        ),
    )
