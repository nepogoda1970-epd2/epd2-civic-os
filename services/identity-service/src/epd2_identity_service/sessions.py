"""Session security.

`SessionRecord` is a **PACK-14 service-level aggregate**. It is not added
to canon and its events use PACK-13's canonical envelope unchanged. The
precedent is PACK-12's `PrivilegedSession`: a session is an operational
fact about a running system, not the kind of governed institutional
record canon holds (OD-P14-05).

Both deadlines are mandatory fields with no `None` and no sentinel, so
**no code path in this package can construct a session without them**.
That is what "no infinite session" means as a property rather than a
promise.

The refresh-token family is the other structural control. A rotated token
is single-use; presenting it again revokes the **whole family** and
raises `SESSION_REPLAY_DETECTED`, because at that point either the holder
or an attacker has a stale copy and there is no safe way to tell which.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.assurance import (
    AuthenticationAssurance,
    RiskState,
    assurance_rank,
)
from epd2_identity_service.configuration import IdentityConfiguration
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    ForbiddenSessionTransitionError,
    SessionExpiredError,
    SessionIdentifierInUrlError,
    SessionOriginMismatchError,
    SessionQuarantinedError,
    SessionReplayDetectedError,
    SessionRevokedError,
    SessionScopeMismatchError,
    UnknownSessionStatusError,
)
from epd2_identity_service.identifiers import (
    AccountId,
    ScopedIdentityReference,
    SessionId,
    require_timezone,
)
from epd2_identity_service.secret_storage import HashedSecret, SecureRandom, hash_token
from epd2_identity_service.workspaces import WorkspaceId, workspace_origin


class SessionStatus(StrEnum):
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    REVOKED = "revoked"
    QUARANTINED = "quarantined"


def parse_session_status(value: str) -> SessionStatus:
    try:
        return SessionStatus(value)
    except ValueError as exc:
        raise UnknownSessionStatusError(f"unknown session status: {value!r}") from exc


_ALLOWED_SESSION_TRANSITIONS: frozenset[tuple[SessionStatus, SessionStatus]] = frozenset(
    {
        (SessionStatus.ACTIVE, SessionStatus.IDLE),
        (SessionStatus.ACTIVE, SessionStatus.EXPIRED),
        (SessionStatus.ACTIVE, SessionStatus.REVOKED),
        (SessionStatus.ACTIVE, SessionStatus.QUARANTINED),
        (SessionStatus.IDLE, SessionStatus.ACTIVE),
        (SessionStatus.IDLE, SessionStatus.EXPIRED),
        (SessionStatus.IDLE, SessionStatus.REVOKED),
        (SessionStatus.IDLE, SessionStatus.QUARANTINED),
        (SessionStatus.QUARANTINED, SessionStatus.REVOKED),
        (SessionStatus.QUARANTINED, SessionStatus.ACTIVE),
        (SessionStatus.EXPIRED, SessionStatus.REVOKED),
    }
)


class RotationTrigger(StrEnum):
    """Why a session was rotated. Each is a mandatory rotation point in
    the session security matrix, and naming them individually is what
    lets a test assert that each one actually rotates."""

    AUTHENTICATION = "authentication"
    STEP_UP = "step_up"
    PRIVILEGE_CHANGE = "privilege_change"
    REFRESH = "refresh"


@dataclass(frozen=True, slots=True)
class DeviceReference:
    """Something the holder can recognise in their session inventory.

    Deliberately **not** a stable cross-domain device identifier: the
    label is per account and the digest is salted per session family, so
    two accounts on one device produce two unrelated references.
    """

    device_label: str
    device_digest: str

    def __post_init__(self) -> None:
        if not self.device_label:
            raise ValueError("a device reference carries a label the holder can recognise")
        if len(self.device_digest) != 64:
            raise ValueError("device_digest must be a 64-character hex digest")


@dataclass(frozen=True, slots=True)
class SessionScope:
    """One workspace, one origin, one capability set.

    A session never spans a risk boundary: crossing into a
    higher-sensitivity workspace requires a new authentication or a
    step-up, never a token exchange.
    """

    workspace: WorkspaceId
    origin: str
    capabilities: frozenset[str]

    def __post_init__(self) -> None:
        if self.origin != workspace_origin(self.workspace):
            raise SessionOriginMismatchError(
                f"{self.origin!r} is not the declared origin of {self.workspace.value}"
            )


@dataclass(frozen=True, slots=True)
class SessionRevocation:
    """Immutable, with a reason code and an actor class."""

    revoked_at: datetime
    reason_code: str
    actor_class: str

    def __post_init__(self) -> None:
        require_timezone(self.revoked_at, "revoked_at")
        if not self.reason_code:
            raise ValueError("a revocation carries a registered reason code")


@dataclass(frozen=True, slots=True)
class RefreshTokenFamily:
    """A rotation chain.

    Only digests are held. `superseded_digests` is what makes reuse
    detectable: presenting any digest in that set is a replay, whatever
    the current token is.
    """

    family_id: UUID
    current_digest: HashedSecret
    superseded_digests: frozenset[str] = frozenset()
    revoked: bool = False

    def rotated(self, new_token: str) -> RefreshTokenFamily:
        return replace(
            self,
            current_digest=hash_token(new_token),
            superseded_digests=self.superseded_digests | {self.current_digest.digest},
        )

    def assert_presentable(self, presented_token: str) -> None:
        """The replay rule.

        A superseded token revokes the family; a token that matches
        neither the current nor a superseded digest is simply not ours
        and is refused as a revoked session rather than as a replay,
        because inventing a replay event from an unrelated string would
        make the replay signal untrustworthy.
        """
        if self.revoked:
            raise SessionRevokedError("this refresh token family has been revoked")
        digest = hash_token(presented_token).digest
        if digest in self.superseded_digests:
            raise SessionReplayDetectedError(
                "a rotated refresh token was presented again; the family is revoked"
            )
        if digest != self.current_digest.digest:
            raise SessionRevokedError("the presented refresh token is not current for this session")


@dataclass(frozen=True, slots=True)
class SessionRecord:
    """The session aggregate.

    `idle_deadline` and `absolute_deadline` are both plain, mandatory
    `datetime`s. There is no nullable variant and no "never expires"
    value anywhere in this module.
    """

    session_id: SessionId
    account_id: AccountId
    actor_reference: ScopedIdentityReference
    scope: SessionScope
    status: SessionStatus
    assurance: AuthenticationAssurance
    issued_at: datetime
    last_activity_at: datetime
    idle_deadline: datetime
    absolute_deadline: datetime
    device: DeviceReference
    risk_state: RiskState
    refresh_family: RefreshTokenFamily
    csrf_token_digest: HashedSecret
    step_up_reference: UUID | None = None
    revocation: SessionRevocation | None = None
    rotation_count: int = 0
    revoked_credential_ids: frozenset[UUID] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        for name in ("issued_at", "last_activity_at", "idle_deadline", "absolute_deadline"):
            require_timezone(getattr(self, name), name)
        if self.absolute_deadline <= self.issued_at:
            raise ValueError("the absolute deadline must follow issuance; no infinite session")
        if self.idle_deadline > self.absolute_deadline:
            raise ValueError("the idle deadline never outlives the absolute one")
        if (self.status is SessionStatus.REVOKED) != (self.revocation is not None):
            raise ValueError("a revoked session carries a revocation record, and only it does")

    def effective_expiry(self) -> datetime:
        return min(self.idle_deadline, self.absolute_deadline)

    def assert_presentable(self, *, origin: str, now: datetime) -> None:
        """The gate every request through this session passes.

        Revocation is checked before expiry deliberately: a revoked
        session that has also expired must still report `SESSION_REVOKED`,
        because "it expired anyway" is not the answer a person asking
        "did my revocation work?" needs.
        """
        moment = require_timezone(now, "now")
        if self.status is SessionStatus.REVOKED:
            raise SessionRevokedError("the session was revoked and cannot be used or refreshed")
        if self.status is SessionStatus.QUARANTINED:
            raise SessionQuarantinedError("the session is quarantined pending a security response")
        if moment >= self.absolute_deadline:
            raise SessionExpiredError("the absolute session deadline has been reached")
        if moment >= self.idle_deadline:
            raise SessionExpiredError("the idle session deadline has been reached")
        if origin != self.scope.origin:
            raise SessionOriginMismatchError(
                f"the session is bound to {self.scope.origin!r}, not {origin!r}"
            )

    def assert_scope(self, workspace: WorkspaceId) -> None:
        if workspace is not self.scope.workspace:
            raise SessionScopeMismatchError(
                f"the session is scoped to {self.scope.workspace.value}, not {workspace.value}"
            )

    def assert_csrf(self, presented_token: str) -> None:
        if not self.csrf_token_digest.matches(presented_token):
            raise SessionRevokedError("a state-changing request lacked a valid CSRF token")

    def assert_transition_allowed(self, target: SessionStatus) -> None:
        if (self.status, target) not in _ALLOWED_SESSION_TRANSITIONS:
            raise ForbiddenSessionTransitionError(
                f"session transition {self.status.value!r} -> {target.value!r} is not allowed"
            )

    def transitioned(self, target: SessionStatus) -> SessionRecord:
        """Only for transitions that need no companion record.

        Revocation deliberately does **not** go through here: a revoked
        session must carry its revocation record, and constructing an
        intermediate without one would break that invariant on the way to
        satisfying it. `revoke_session` applies both in a single
        construction instead.
        """
        self.assert_transition_allowed(target)
        return replace(self, status=target)


def issue_session(
    *,
    session_id: SessionId,
    account_id: AccountId,
    actor_reference: ScopedIdentityReference,
    scope: SessionScope,
    assurance: AuthenticationAssurance,
    device: DeviceReference,
    issued_at: datetime,
    configuration: IdentityConfiguration,
    random: SecureRandom,
) -> tuple[SessionRecord, str, str]:
    """Issue a session; return the record and the two secrets exactly
    once.

    The refresh token and the CSRF token are returned as plaintext to the
    caller and stored only as digests. Deadlines come from the governed
    configuration keyed by the **effective** assurance, so a downgraded
    session gets the shorter window its level deserves rather than the
    one its login earned.
    """
    moment = require_timezone(issued_at, "issued_at")
    level = assurance.effective_level
    if level is AuthenticationAssuranceLevel.NONE:
        raise SessionRevokedError("an unauthenticated context does not produce a session")
    refresh_token = random.token()
    csrf_token = random.token()
    record = SessionRecord(
        session_id=session_id,
        account_id=account_id,
        actor_reference=actor_reference,
        scope=scope,
        status=SessionStatus.ACTIVE,
        assurance=assurance,
        issued_at=moment,
        last_activity_at=moment,
        idle_deadline=moment + configuration.idle_timeout(level),
        absolute_deadline=moment + configuration.absolute_timeout(level),
        device=device,
        risk_state=assurance.evidence.risk_state,
        refresh_family=RefreshTokenFamily(
            family_id=session_id, current_digest=hash_token(refresh_token)
        ),
        csrf_token_digest=hash_token(csrf_token),
    )
    return record, refresh_token, csrf_token


def rotate_session(
    session: SessionRecord,
    *,
    new_session_id: SessionId,
    trigger: RotationTrigger,
    rotated_at: datetime,
    configuration: IdentityConfiguration,
    random: SecureRandom,
) -> tuple[SessionRecord, str]:
    """Rotation after authentication, step-up and privilege change.

    The session **identifier itself** changes, not merely the refresh
    token: session fixation is defeated by the identifier the browser
    holds becoming worthless, and rotating only the refresh token would
    leave a fixed session ID in place.
    """
    moment = require_timezone(rotated_at, "rotated_at")
    session.assert_presentable(origin=session.scope.origin, now=moment)
    refresh_token = random.token()
    level = session.assurance.effective_level
    rotated = replace(
        session,
        session_id=new_session_id,
        issued_at=session.issued_at,
        last_activity_at=moment,
        idle_deadline=moment + configuration.idle_timeout(level),
        refresh_family=session.refresh_family.rotated(refresh_token),
        rotation_count=session.rotation_count + 1,
        step_up_reference=None
        if trigger is RotationTrigger.PRIVILEGE_CHANGE
        else session.step_up_reference,
    )
    return rotated, refresh_token


def refresh_session(
    session: SessionRecord,
    *,
    presented_refresh_token: str,
    refreshed_at: datetime,
    configuration: IdentityConfiguration,
    random: SecureRandom,
) -> tuple[SessionRecord, str]:
    """Refresh, with replay detection.

    A revoked session refuses here before anything else happens - the
    acceptance blocker "session revoke does not block refresh" is exactly
    this call, and `assert_presentable` is what closes it.
    """
    moment = require_timezone(refreshed_at, "refreshed_at")
    session.assert_presentable(origin=session.scope.origin, now=moment)
    session.refresh_family.assert_presentable(presented_refresh_token)
    new_token = random.token()
    level = session.assurance.effective_level
    refreshed = replace(
        session,
        last_activity_at=moment,
        idle_deadline=moment + configuration.idle_timeout(level),
        refresh_family=session.refresh_family.rotated(new_token),
    )
    if refreshed.idle_deadline > refreshed.absolute_deadline:
        refreshed = replace(refreshed, idle_deadline=refreshed.absolute_deadline)
    return refreshed, new_token


def revoke_session(
    session: SessionRecord, *, reason_code: str, actor_class: str, revoked_at: datetime
) -> SessionRecord:
    revocation = SessionRevocation(
        revoked_at=require_timezone(revoked_at, "revoked_at"),
        reason_code=reason_code,
        actor_class=actor_class,
    )
    session.assert_transition_allowed(SessionStatus.REVOKED)
    return replace(
        session,
        status=SessionStatus.REVOKED,
        revocation=revocation,
        refresh_family=replace(session.refresh_family, revoked=True),
    )


def revoke_all_sessions(
    sessions: tuple[SessionRecord, ...],
    *,
    reason_code: str,
    actor_class: str,
    revoked_at: datetime,
) -> tuple[SessionRecord, ...]:
    """Revoke every session for an account.

    Partial revocation is treated as failure by the caller (workflow
    matrix §4): this function revokes every revocable session and the
    application layer reports the count, so "some sessions survived" can
    never be reported as complete.
    """
    return tuple(
        revoke_session(
            session, reason_code=reason_code, actor_class=actor_class, revoked_at=revoked_at
        )
        if session.status is not SessionStatus.REVOKED
        else session
        for session in sessions
    )


def revoke_sessions_for_credential(
    sessions: tuple[SessionRecord, ...],
    *,
    credential_id: UUID,
    reason_code: str,
    actor_class: str,
    revoked_at: datetime,
) -> tuple[SessionRecord, ...]:
    """A compromised credential invalidates the sessions it could have
    produced.

    "Could have produced" rather than "did produce": the credential that
    authenticated a session is recorded, and any session whose assurance
    rests on the revoked credential goes, because a narrower rule leaves
    the attacker exactly the session they are using.
    """
    return tuple(
        revoke_session(
            session, reason_code=reason_code, actor_class=actor_class, revoked_at=revoked_at
        )
        if credential_id in session.revoked_credential_ids | {credential_id}
        and session.status is not SessionStatus.REVOKED
        else session
        for session in sessions
    )


def change_assurance(
    session: SessionRecord,
    *,
    assurance: AuthenticationAssurance,
    changed_at: datetime,
    configuration: IdentityConfiguration,
) -> SessionRecord:
    """Raise or downgrade a session's assurance.

    A downgrade shortens the deadlines to the new level's, because a
    session that lost its factor should not keep the eight-hour window
    the factor bought it. It does **not** end the session: it leaves one
    that can still do what it satisfies.
    """
    moment = require_timezone(changed_at, "changed_at")
    level = assurance.effective_level
    new_idle = moment + configuration.idle_timeout(level)
    new_absolute = session.issued_at + configuration.absolute_timeout(level)
    downgraded = assurance_rank(level) < assurance_rank(session.assurance.effective_level)
    return replace(
        session,
        assurance=assurance,
        risk_state=assurance.evidence.risk_state,
        idle_deadline=min(new_idle, session.idle_deadline) if downgraded else new_idle,
        absolute_deadline=(
            min(new_absolute, session.absolute_deadline)
            if downgraded
            else session.absolute_deadline
        ),
        step_up_reference=None if downgraded else session.step_up_reference,
    )


def mark_suspicious(session: SessionRecord) -> SessionRecord:
    return replace(session.transitioned(SessionStatus.QUARANTINED), risk_state=RiskState.SUSPICIOUS)


def refuse_session_identifier_in_url(url: str) -> None:
    """No session identifier ever appears in a URL.

    Called by the redirect-construction path. URLs end up in logs,
    referrer headers and shoulder views, and a session ID in one is a
    session ID in all three.
    """
    lowered = url.lower()
    for marker in ("session_id=", "sessionid=", "sid=", "refresh_token=", "csrf_token="):
        if marker in lowered:
            raise SessionIdentifierInUrlError(
                f"a session identifier may not appear in a URL (found {marker!r})"
            )


@dataclass(frozen=True, slots=True)
class SessionCookieAttributes:
    """The attributes every session cookie carries.

    All three security attributes are `True` with no way to construct
    them otherwise; `same_site` admits only `Strict` and `Lax`, and
    `domain` is always the exact workspace host - never a parent domain,
    because a parent-domain cookie is precisely the shared session this
    architecture refuses (`§11.1`, rule 4).
    """

    name: str
    host: str
    secure: bool = True
    http_only: bool = True
    same_site: str = "Strict"
    path: str = "/"

    def __post_init__(self) -> None:
        if not self.secure or not self.http_only:
            raise ValueError("session cookies are always Secure and HttpOnly")
        if self.same_site not in ("Strict", "Lax"):
            raise ValueError("session cookies use SameSite=Strict or SameSite=Lax")
        if self.host.startswith("."):
            raise ValueError("no parent-domain cookie is ever issued for a workspace")


def session_cookie_for(
    workspace: WorkspaceId, *, name: str = "epd2_session"
) -> SessionCookieAttributes:
    origin = workspace_origin(workspace)
    host = origin.removeprefix("https://").removeprefix("http://")
    return SessionCookieAttributes(name=name, host=host)


def session_idle_extension(
    configuration: IdentityConfiguration, level: AuthenticationAssuranceLevel
) -> timedelta:
    return configuration.idle_timeout(level)
