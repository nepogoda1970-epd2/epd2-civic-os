"""W2 — authority source and read models.

The directory is the current-state projection over an append-only journal of
authority source records. `current_*` answers "what is true now"; `history_of`
answers "what was recorded, in order". A state change appends; it never edits
or removes a prior record, so a read model can summarise the present without
erasing the past (`FIR-TRUST-002` section 6, W2 constraint).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from epd2_control_plane_service.domain import (
    AuthorityState,
    CredentialState,
    OrganizationalAuthority,
    RegionalAdministrationRestriction,
    Right,
    Scope,
    ServiceCredential,
    Session,
    SessionState,
    TemporarySupervision,
    TrustKeyReference,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.policy import ControlPolicy

__all__ = ["AuthorityDirectory", "AuthorityRecord", "AuthorityResolution"]


@dataclass(frozen=True, slots=True)
class AuthorityRecord:
    """One immutable entry in the authority source journal."""

    sequence: int
    recorded_at: datetime
    authority_id: str
    state: AuthorityState
    rule_version: str
    source_decision_ref: str
    recorded_by: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class AuthorityResolution:
    """The outcome of resolving a principal's authority for one act.

    A refusal carries its reason code so that the caller records evidence of the
    refusal rather than discarding it.
    """

    granted: bool
    authority: OrganizationalAuthority | None
    reason_code: str
    detail: str = ""

    @property
    def authority_basis(self) -> str:
        if self.authority is None:
            return "NONE"
        authority = self.authority
        return f"{authority.authority_id}@{authority.rule_version}#{authority.source_decision_ref}"


class AuthorityDirectory:
    """Authority, session, credential, restriction and trust read models."""

    def __init__(self, policy: ControlPolicy | None = None) -> None:
        self._policy = policy or ControlPolicy.governed()
        self._authorities: dict[str, OrganizationalAuthority] = {}
        self._journal: list[AuthorityRecord] = []
        self._sessions: dict[str, Session] = {}
        self._restrictions: dict[str, RegionalAdministrationRestriction] = {}
        self._supervisions: dict[str, TemporarySupervision] = {}
        self._service_credentials: dict[str, ServiceCredential] = {}
        self._human_credentials: dict[str, tuple[str, CredentialState, str | None]] = {}
        self._key_references: dict[str, TrustKeyReference] = {}

    # -- authority ----------------------------------------------------------

    def record_authority(
        self,
        authority: OrganizationalAuthority,
        *,
        recorded_at: datetime,
        recorded_by: str,
        note: str = "",
    ) -> None:
        self._authorities[authority.authority_id] = authority
        self._journal.append(
            AuthorityRecord(
                sequence=len(self._journal) + 1,
                recorded_at=recorded_at,
                authority_id=authority.authority_id,
                state=authority.state,
                rule_version=authority.rule_version,
                source_decision_ref=authority.source_decision_ref,
                recorded_by=recorded_by,
                note=note,
            )
        )

    def set_authority_state(
        self,
        authority_id: str,
        state: AuthorityState,
        *,
        recorded_at: datetime,
        recorded_by: str,
        note: str = "",
    ) -> OrganizationalAuthority:
        current = self._authorities[authority_id]
        updated = current.with_state(state)
        self.record_authority(updated, recorded_at=recorded_at, recorded_by=recorded_by, note=note)
        return updated

    def current_authority(self, authority_id: str) -> OrganizationalAuthority | None:
        return self._authorities.get(authority_id)

    def authorities_of(self, subject_ref: str) -> tuple[OrganizationalAuthority, ...]:
        return tuple(a for a in self._authorities.values() if a.subject_ref == subject_ref)

    def history_of(self, authority_id: str) -> tuple[AuthorityRecord, ...]:
        return tuple(r for r in self._journal if r.authority_id == authority_id)

    def journal(self) -> tuple[AuthorityRecord, ...]:
        return tuple(self._journal)

    # -- sessions, credentials, keys ----------------------------------------

    def put_session(self, session: Session) -> None:
        self._sessions[session.session_id] = session

    def set_session_state(self, session_id: str, state: SessionState) -> Session:
        current = self._sessions[session_id]
        updated = Session(
            session_id=current.session_id,
            principal_id=current.principal_id,
            state=state,
            established_at=current.established_at,
            assurance_level=current.assurance_level,
        )
        self._sessions[session_id] = updated
        return updated

    def session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def put_service_credential(self, credential: ServiceCredential) -> None:
        self._service_credentials[credential.credential_id] = credential

    def service_credential(self, credential_id: str) -> ServiceCredential | None:
        return self._service_credentials.get(credential_id)

    def put_human_credential(
        self, credential_id: str, subject_ref: str, state: CredentialState
    ) -> None:
        self._human_credentials[credential_id] = (subject_ref, state, None)

    def set_human_credential_state(
        self, credential_id: str, state: CredentialState, *, replaced_by: str | None = None
    ) -> None:
        subject_ref, current, existing_replacement = self._human_credentials[credential_id]
        terminal = {CredentialState.REVOKED, CredentialState.REPLACED, CredentialState.DESTROYED}
        if current in terminal and state is CredentialState.ACTIVE:
            # FIR-SEC-004: a revoked or replaced credential is never silently
            # resurrected under the same credential identity.
            raise AuthorizationRefused(
                (
                    f"credential {credential_id} is {current.value} and cannot be reactivated "
                    f"under the same identity"
                ),
                reason_code="CTRL_CREDENTIAL_RESURRECTION",
            )
        self._human_credentials[credential_id] = (
            subject_ref,
            state,
            replaced_by or existing_replacement,
        )

    def human_credential(
        self, credential_id: str
    ) -> tuple[str, CredentialState, str | None] | None:
        return self._human_credentials.get(credential_id)

    def credentials_of(self, subject_ref: str) -> tuple[tuple[str, CredentialState], ...]:
        return tuple(
            (cid, state)
            for cid, (subject, state, _) in self._human_credentials.items()
            if subject == subject_ref
        )

    def put_key_reference(self, reference: TrustKeyReference) -> None:
        self._key_references[reference.key_reference_id] = reference

    def key_reference(self, key_reference_id: str) -> TrustKeyReference | None:
        return self._key_references.get(key_reference_id)

    # -- interventions ------------------------------------------------------

    def put_restriction(self, restriction: RegionalAdministrationRestriction) -> None:
        self._restrictions[restriction.restriction_id] = restriction

    def restriction(self, restriction_id: str) -> RegionalAdministrationRestriction | None:
        return self._restrictions.get(restriction_id)

    def restrictions(self) -> tuple[RegionalAdministrationRestriction, ...]:
        return tuple(self._restrictions.values())

    def active_restrictions(
        self, moment: datetime
    ) -> tuple[RegionalAdministrationRestriction, ...]:
        return tuple(r for r in self._restrictions.values() if r.is_active_at(moment))

    def put_supervision(self, supervision: TemporarySupervision) -> None:
        self._supervisions[supervision.supervision_id] = supervision

    def supervisions(self) -> tuple[TemporarySupervision, ...]:
        return tuple(self._supervisions.values())

    def blocking_restriction(
        self, action_id: str, scope: Scope, authority_id: str | None, moment: datetime
    ) -> RegionalAdministrationRestriction | None:
        if not self._policy.enforce_interventions:
            return None
        for restriction in self._restrictions.values():
            if restriction.is_active_at(moment) and restriction.restricts(
                action_id, scope, authority_id
            ):
                return restriction
        return None

    # -- resolution ---------------------------------------------------------

    def resolve(
        self,
        *,
        subject_ref: str,
        required_right: Right,
        action_id: str,
        scope: Scope,
        moment: datetime,
    ) -> AuthorityResolution:
        """Resolve current authority for one exact act.

        Order matters: scope isolation is checked before capability, so that a
        Bund office holding the capability in its own scope can never be
        reported as "capable but out of scope" in a way a caller might treat as
        a soft failure. Every negative outcome is a hard refusal.
        """
        candidates = self.authorities_of(subject_ref)
        if not candidates:
            return AuthorityResolution(
                False, None, "CTRL_NO_AUTHORITY", f"{subject_ref} holds no governed authority"
            )

        scope_matched: list[OrganizationalAuthority] = []
        for authority in candidates:
            if not self._policy.enforce_scope_isolation:
                scope_matched.append(authority)
                continue
            if authority.scope.contains(scope):
                scope_matched.append(authority)
                continue
            # Cross-scope reach exists only where the authority carries an
            # explicit oversight grant that matches the scope its source
            # decision names. One decision authorises exactly one target scope,
            # so both a widened grant and a re-pointed grant fail closed.
            if scope.key in authority.oversight_of:
                if self._policy.enforce_oversight_binding and authority.oversight_of != frozenset(
                    {authority.oversight_decision_scope}
                ):
                    continue
                scope_matched.append(authority)

        if not scope_matched:
            return AuthorityResolution(
                False,
                None,
                "CTRL_SCOPE_ISOLATION",
                f"no authority of {subject_ref} covers scope {scope.key}; hierarchy grants nothing",
            )

        capable = [
            a
            for a in scope_matched
            if required_right in a.capabilities and action_id in a.action_codes
        ]
        if not capable:
            return AuthorityResolution(
                False,
                None,
                "CTRL_CAPABILITY_ABSENT",
                f"no authority of {subject_ref} carries {required_right.value} for {action_id}",
            )

        effective = (
            [a for a in capable if a.is_effective_at(moment)]
            if self._policy.enforce_authority_state
            else capable
        )
        if not effective:
            state = capable[0].state.value
            reason = {
                AuthorityState.SUSPENDED.value: "CTRL_AUTHORITY_SUSPENDED",
                AuthorityState.REVOKED.value: "CTRL_AUTHORITY_REVOKED",
                AuthorityState.EXPIRED.value: "CTRL_AUTHORITY_EXPIRED",
            }.get(state, "CTRL_AUTHORITY_NOT_EFFECTIVE")
            if capable[0].state is AuthorityState.ACTIVE:
                reason = "CTRL_AUTHORITY_EXPIRED"
            return AuthorityResolution(
                False,
                None,
                reason,
                f"authority for {action_id} is not effective at {moment.isoformat()}",
            )

        return AuthorityResolution(True, effective[0], "CTRL_AUTHORIZED")

    # -- read model export --------------------------------------------------

    def read_model(self, moment: datetime) -> dict[str, Any]:
        """The W2 read model. Summarises current state; never erases history."""
        return {
            "schema": "epd2.ctrl01.authority-read-model/1",
            "as_of": moment.isoformat(),
            "current_organizational_authority": [
                {
                    "authority_id": a.authority_id,
                    "subject_ref": a.subject_ref,
                    "office_code": a.office_code,
                    "scope": a.scope.key,
                    "capabilities": sorted(r.value for r in a.capabilities),
                    "action_codes": sorted(a.action_codes),
                    "state": a.state.value,
                    "effective_now": a.is_effective_at(moment),
                    "oversight_of": sorted(a.oversight_of),
                    "oversight_decision_scope": a.oversight_decision_scope,
                }
                for a in sorted(self._authorities.values(), key=lambda x: x.authority_id)
            ],
            "authority_source": [
                {
                    "authority_id": a.authority_id,
                    "rule_version": a.rule_version,
                    "source_decision_ref": a.source_decision_ref,
                    "appointed_by_ref": a.appointed_by_ref,
                    "valid_from": a.valid_from.isoformat(),
                    "valid_until": None if a.valid_until is None else a.valid_until.isoformat(),
                    "evidence_refs": list(a.evidence_refs),
                }
                for a in sorted(self._authorities.values(), key=lambda x: x.authority_id)
            ],
            "authority_history": [
                {
                    "sequence": r.sequence,
                    "recorded_at": r.recorded_at.isoformat(),
                    "authority_id": r.authority_id,
                    "state": r.state.value,
                    "rule_version": r.rule_version,
                    "source_decision_ref": r.source_decision_ref,
                    "recorded_by": r.recorded_by,
                    "note": r.note,
                }
                for r in self._journal
            ],
            "session_quarantine_state": [
                {"session_id": s.session_id, "principal_id": s.principal_id, "state": s.state.value}
                for s in sorted(self._sessions.values(), key=lambda x: x.session_id)
            ],
            "current_restrictions": [
                {
                    "restriction_id": r.restriction_id,
                    "intervention_type": r.intervention_type.value,
                    "target_scope": r.target_scope.key,
                    "affected_action_codes": sorted(r.affected_action_codes),
                    "affected_authority_ids": sorted(r.affected_authority_ids),
                    "valid_from": r.valid_from.isoformat(),
                    "valid_until": None if r.valid_until is None else r.valid_until.isoformat(),
                    "reason_code": r.reason_code,
                    "decision_ref": r.decision_ref,
                    "review_deadline": r.review_deadline.isoformat(),
                    "active_now": r.is_active_at(moment),
                }
                for r in sorted(self._restrictions.values(), key=lambda x: x.restriction_id)
            ],
            "temporary_supervision": [
                {
                    "supervision_id": s.supervision_id,
                    "supervised_scope": s.supervised_scope.key,
                    "supervisor_authority_id": s.supervisor_authority_id,
                    "granted_action_codes": sorted(s.granted_action_codes),
                    "valid_until": s.valid_until.isoformat(),
                    "confirmation_organ": s.confirmation_organ,
                    "active_now": s.is_active_at(moment),
                }
                for s in sorted(self._supervisions.values(), key=lambda x: x.supervision_id)
            ],
            "service_credential_state": [
                {
                    "credential_id": c.credential_id,
                    "holder_service": c.holder_service,
                    "class": c.credential_class.value,
                    "state": c.state.value,
                    "scope": c.scope.key,
                }
                for c in sorted(self._service_credentials.values(), key=lambda x: x.credential_id)
            ],
            "human_credential_state": [
                {
                    "credential_id": cid,
                    "subject_ref": subject,
                    "state": state.value,
                    "replaced_by": replaced,
                }
                for cid, (subject, state, replaced) in sorted(self._human_credentials.items())
            ],
            "trust_key_references": [
                {
                    "key_reference_id": k.key_reference_id,
                    "key_class": k.key_class,
                    "credential_class": k.credential_class.value,
                    "algorithm": k.algorithm,
                    "trust_state": k.trust_state,
                    "custody_policy_ref": k.custody_policy_ref,
                    "exportable": k.exportable,
                    "threshold": None if k.quorum_m is None else f"{k.quorum_m}-of-{k.quorum_n}",
                }
                for k in sorted(self._key_references.values(), key=lambda x: x.key_reference_id)
            ],
        }


def summarize_scopes(authorities: Iterable[OrganizationalAuthority]) -> Mapping[str, int]:
    counts: dict[str, int] = {}
    for authority in authorities:
        counts[authority.scope.key] = counts.get(authority.scope.key, 0) + 1
    return counts
