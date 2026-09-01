"""The governed scoped-attribute adapter (PACK-15 specification section 9).

The Eligibility Service receives **the answer, not the data the answer was
computed from**. `age_threshold_met = true` leaks one bit;
`date_of_birth = 1974-03-11` leaks a quasi-identifier that outlives the
vote in every log it touches.

Two structural rules, both enforced here rather than by review:

1. **An attribute the frozen rule-set version does not declare is
   refused**, never silently dropped - a dropped attribute still travelled
   through a transport, a deserializer and, on a bad day, an error report.
2. **An attribute on the prohibited set is refused as a boundary
   violation**, and the refusal names the attribute rather than the value,
   because naming the value in the refusal would be the leak.

This module holds no state, performs no I/O and imports nothing from
`epd2_membership_service` or `epd2_identity_service` - the absence of an
import path is what makes the boundary structural rather than procedural.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from epd2_eligibility_service.voting_trust_exceptions import (
    ProhibitedAttributeError,
    UndeclaredAttributeError,
)

#: Never delivered to any PACK-15 component, in any form, in any encoding.
#: The prohibition is on *derivability*: a hash of the member number is
#: the member number.
PROHIBITED_ATTRIBUTE_NAMES: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "person_record_id",
        "identity_record_id",
        "membership_id",
        "member_number",
        "email",
        "phone",
        "full_name",
        "name",
        "given_name",
        "family_name",
        "date_of_birth",
        "birth_date",
        "address",
        "postal_address",
        "communication_persona_id",
        "eid_subject",
        "identity_provider_reference",
        "member_record",
        "membership_record",
    }
)

#: The complete set of minimized attributes a rule-set version may declare.
#: Every entry is a predicate or a closed enumeration evaluated **at the
#: source**; none is a value from which a person can be recognised.
PERMITTED_ATTRIBUTE_NAMES: frozenset[str] = frozenset(
    {
        "membership_active",
        "membership_duration_requirement_met",
        "membership_effective_since_bucket",
        "organization_scope",
        "organizational_level_class",
        "required_role_held",
        "age_threshold_met",
        "participation_restricted",
        "restriction_class",
        "participation_class",
        "conflict_declared",
        "is_candidate_in_context",
        "required_assurance_satisfied",
        "manual_exception_granted",
        "governed_rule_outcome",
    }
)


class AttributeKind(StrEnum):
    """How an attribute is permitted to be shaped."""

    PREDICATE = "predicate"
    SCOPE_REFERENCE = "scope_reference"
    ENUMERATION = "enumeration"
    BUCKET = "bucket"


#: The declared shape of every permitted attribute. A permitted name
#: delivered in the wrong shape is refused: `membership_active: "active"`
#: is a record field wearing a predicate's name.
ATTRIBUTE_KINDS: Mapping[str, AttributeKind] = {
    "membership_active": AttributeKind.PREDICATE,
    "membership_duration_requirement_met": AttributeKind.PREDICATE,
    "membership_effective_since_bucket": AttributeKind.BUCKET,
    "organization_scope": AttributeKind.SCOPE_REFERENCE,
    "organizational_level_class": AttributeKind.ENUMERATION,
    "required_role_held": AttributeKind.PREDICATE,
    "age_threshold_met": AttributeKind.PREDICATE,
    "participation_restricted": AttributeKind.PREDICATE,
    "restriction_class": AttributeKind.ENUMERATION,
    "participation_class": AttributeKind.ENUMERATION,
    "conflict_declared": AttributeKind.PREDICATE,
    "is_candidate_in_context": AttributeKind.PREDICATE,
    "required_assurance_satisfied": AttributeKind.PREDICATE,
    "manual_exception_granted": AttributeKind.PREDICATE,
    "governed_rule_outcome": AttributeKind.ENUMERATION,
}


class EligibilitySourceVersionMissingError(UndeclaredAttributeError):
    """A scoped attribute without a source-data version reference.

    A decision that cannot name the version of the facts it relied on
    cannot be re-evaluated when those facts change, which is the
    invalidation rule of specification section 8.2.
    """


@dataclass(frozen=True, slots=True)
class ScopedAttribute:
    """One minimized attribute, as delivered by the governed adapter."""

    name: str
    kind: AttributeKind
    predicate_value: bool | None = None
    enumeration_value: str | None = None
    scope_reference: str | None = None
    bucket_value: str | None = None
    source_owner: str = ""
    source_version: str = ""

    def __post_init__(self) -> None:
        if self.name in PROHIBITED_ATTRIBUTE_NAMES:
            raise ProhibitedAttributeError(
                f"{self.name!r} is on the prohibited identity set and may not be delivered"
            )
        if self.name not in PERMITTED_ATTRIBUTE_NAMES:
            raise UndeclaredAttributeError(f"{self.name!r} is not a permitted scoped attribute")
        if ATTRIBUTE_KINDS[self.name] is not self.kind:
            raise UndeclaredAttributeError(
                f"{self.name!r} must be delivered as {ATTRIBUTE_KINDS[self.name].value}"
            )
        if not self.source_owner:
            raise UndeclaredAttributeError(f"{self.name!r} must name the owner that evaluated it")
        if not self.source_version:
            raise EligibilitySourceVersionMissingError(
                f"{self.name!r} must name the source-data version it was evaluated against"
            )
        self._assert_single_shape()

    def _assert_single_shape(self) -> None:
        present = [
            field_name
            for field_name, value in (
                ("predicate_value", self.predicate_value),
                ("enumeration_value", self.enumeration_value),
                ("scope_reference", self.scope_reference),
                ("bucket_value", self.bucket_value),
            )
            if value is not None
        ]
        if len(present) != 1:
            raise UndeclaredAttributeError(
                f"{self.name!r} carries exactly one value field, not {present}"
            )
        expected = {
            AttributeKind.PREDICATE: "predicate_value",
            AttributeKind.ENUMERATION: "enumeration_value",
            AttributeKind.SCOPE_REFERENCE: "scope_reference",
            AttributeKind.BUCKET: "bucket_value",
        }[self.kind]
        if present[0] != expected:
            raise UndeclaredAttributeError(
                f"{self.name!r} is a {self.kind.value} and must use {expected}"
            )


def predicate(name: str, value: bool, *, source_owner: str, source_version: str) -> ScopedAttribute:
    """Build a predicate attribute - the shape most rows should use."""
    return ScopedAttribute(
        name=name,
        kind=AttributeKind.PREDICATE,
        predicate_value=value,
        source_owner=source_owner,
        source_version=source_version,
    )


def enumeration(
    name: str, value: str, *, source_owner: str, source_version: str
) -> ScopedAttribute:
    return ScopedAttribute(
        name=name,
        kind=AttributeKind.ENUMERATION,
        enumeration_value=value,
        source_owner=source_owner,
        source_version=source_version,
    )


def scope(name: str, value: str, *, source_owner: str, source_version: str) -> ScopedAttribute:
    return ScopedAttribute(
        name=name,
        kind=AttributeKind.SCOPE_REFERENCE,
        scope_reference=value,
        source_owner=source_owner,
        source_version=source_version,
    )


def bucket(name: str, value: str, *, source_owner: str, source_version: str) -> ScopedAttribute:
    return ScopedAttribute(
        name=name,
        kind=AttributeKind.BUCKET,
        bucket_value=value,
        source_owner=source_owner,
        source_version=source_version,
    )


def reject_prohibited_attribute_names(payload: Mapping[str, object]) -> None:
    """Refuse a mapping carrying any prohibited identity attribute.

    Applied at the adapter boundary before anything is read, so that a
    prohibited attribute never reaches a field, a log or an event.
    """
    offending = sorted(set(payload) & PROHIBITED_ATTRIBUTE_NAMES)
    if offending:
        raise ProhibitedAttributeError(
            "prohibited identity attributes offered to the eligibility adapter: "
            + ", ".join(offending)
        )


def ingest_scoped_attributes(
    payload: Mapping[str, object],
    *,
    declared_names: frozenset[str],
    source_owner: str,
    source_version: str,
) -> tuple[ScopedAttribute, ...]:
    """Turn an attestation mapping into validated scoped attributes.

    `declared_names` is the input set the **frozen rule-set version**
    declares. An attribute outside it is refused rather than ignored.
    """
    reject_prohibited_attribute_names(payload)
    undeclared = sorted(set(payload) - declared_names)
    if undeclared:
        raise UndeclaredAttributeError(
            "attributes not declared by this rule-set version: " + ", ".join(undeclared)
        )
    attributes: list[ScopedAttribute] = []
    for name in sorted(payload):
        raw = payload[name]
        kind = ATTRIBUTE_KINDS.get(name)
        if kind is None:
            raise UndeclaredAttributeError(f"{name!r} is not a permitted scoped attribute")
        if kind is AttributeKind.PREDICATE:
            if not isinstance(raw, bool):
                raise UndeclaredAttributeError(
                    f"{name!r} is a predicate and must be delivered as a boolean, "
                    "never as the value it was computed from"
                )
            attributes.append(
                predicate(name, raw, source_owner=source_owner, source_version=source_version)
            )
            continue
        if not isinstance(raw, str) or not raw:
            raise UndeclaredAttributeError(f"{name!r} must be delivered as a non-empty string")
        if kind is AttributeKind.ENUMERATION:
            attributes.append(
                enumeration(name, raw, source_owner=source_owner, source_version=source_version)
            )
        elif kind is AttributeKind.SCOPE_REFERENCE:
            attributes.append(
                scope(name, raw, source_owner=source_owner, source_version=source_version)
            )
        else:
            attributes.append(
                bucket(name, raw, source_owner=source_owner, source_version=source_version)
            )
    return tuple(attributes)
