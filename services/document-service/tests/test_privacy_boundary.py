"""The privacy, content and voting-isolation boundaries, swept over the
whole package rather than checked one call site at a time.

These are the tests that would catch a *future* leak: they walk the actual
source, the actual dataclass fields and the actual emitted payloads of a
full lifecycle, so a field or a builder added later is covered without
anybody remembering to add a test for it.

Invariants under test: FIR-INV-001 (no global user ID), FIR-INV-002 and
FIR-INV-003 (identity/ballot unlinkability and voting-client isolation),
FIR-INV-013 (organizational scope isolation), and canon 19f.22's ownership
rule that PACK-11 holds document content — which is exactly why content
must not travel.
"""

from __future__ import annotations

import ast
import re
from dataclasses import fields, is_dataclass
from pathlib import Path
from uuid import uuid4

import pytest
from _builders import (
    Fixture,
    T0,
    at,
    clock_at,
    provenance,
    reason,
    retention_binding,
)

import epd2_document_service
from epd2_document_service import application as app
from epd2_document_service.determinations import SignatureForm, SignatureStatus
from epd2_document_service.domain import (
    FORBIDDEN_CONTENT_KEYS,
    PROHIBITED_IDENTITY_KEYS,
    PROHIBITED_VOTING_KEYS,
    AccessProfile,
    DocumentKind,
    SensitivityClass,
    assert_emission_safe,
)
from epd2_document_service.exceptions import RestrictedAccessDeniedError

SRC = Path(epd2_document_service.__file__).resolve().parent

#: Every module of the service, so a new one is swept automatically.
MODULE_PATHS = sorted(SRC.glob("*.py"))


# ---------------------------------------------------------------------------
# Source-level sweeps
# ---------------------------------------------------------------------------


def test_the_package_defines_no_identity_field_anywhere() -> None:
    """FIR-INV-001, checked structurally.

    A dataclass field named `user_id`, `member_id`, `email` or similar
    would be a global correlation key regardless of whether any payload
    ever emitted it. The check is over declarations, not payloads, so a
    field that exists but is not yet emitted is still caught."""
    offenders: list[str] = []
    for path in MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^\s{4}([a-z_][a-z0-9_]*)\s*:", source, flags=re.MULTILINE):
            name = match.group(1)
            if name in PROHIBITED_IDENTITY_KEYS:
                offenders.append(f"{path.name}:{name}")
    # The vocabulary constants themselves are string literals, not fields,
    # so they cannot appear here.
    assert offenders == [], offenders


def test_the_package_declares_no_voting_field_anywhere() -> None:
    """FIR-INV-002 / FIR-INV-003. A minutes document may *record* that a
    vote happened; it may never hold a reference that could join a ballot
    to a person."""
    offenders: list[str] = []
    for path in MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^\s{4}([a-z_][a-z0-9_]*)\s*:", source, flags=re.MULTILINE):
            if match.group(1) in PROHIBITED_VOTING_KEYS:
                offenders.append(f"{path.name}:{match.group(1)}")
    assert offenders == [], offenders


def test_the_package_imports_no_other_service() -> None:
    """The typed-reference boundary, enforced as an import restriction.

    `document-service` may import `epd2_core`, `epd2_audit_core` and
    itself. Importing `epd2_compliance_service` would turn what canon
    19f.22 says must be "a typed reference and a published interface" into
    a cross-service code edge - which is why `references.py` mirrors
    PACK-09's shapes instead of importing them."""
    allowed = {"epd2_core", "epd2_audit_core", "epd2_document_service"}
    offenders: list[str] = []
    for path in MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^(?:from|import)\s+(epd2_[a-z_]+)", source, flags=re.MULTILINE):
            if match.group(1) not in allowed:
                offenders.append(f"{path.name}: {match.group(1)}")
    assert offenders == [], offenders


def test_no_module_reads_system_time_directly() -> None:
    """A `Clock` is injected into every command, so no governed timestamp
    can depend on when the process happened to run."""
    offenders: list[str] = []
    for path in MODULE_PATHS:
        source = path.read_text(encoding="utf-8")
        for pattern in (r"datetime\.now\(", r"datetime\.utcnow\(", r"time\.time\("):
            if re.search(pattern, source):
                offenders.append(f"{path.name}: {pattern}")
    assert offenders == [], offenders


#: Parameter and variable names that would amount to a switch capable of
#: turning a governed check off.
BREAK_GLASS_NAMES = frozenset(
    {"force", "skip_checks", "skip_authorization", "bypass", "feature_flag", "override_checks"}
)


def test_no_module_offers_a_break_glass_switch() -> None:
    """FIR-INV-006: separation of duties a flag can disable was never in
    force.

    Checked over the parsed AST rather than the raw text, so that
    `NO_BREAK_GLASS_NOTE` - which *names* these switches in order to
    forbid them - does not trip its own test. A prose mention is the
    opposite of a bypass, and a text-matching check cannot tell the two
    apart."""
    offenders: list[str] = []
    for path in MODULE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.arg) and node.arg in BREAK_GLASS_NAMES:
                offenders.append(f"{path.name}: parameter {node.arg}")
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id in BREAK_GLASS_NAMES:
                    offenders.append(f"{path.name}: assignment to {node.id}")
            elif isinstance(node, ast.Attribute) and node.attr == "environ":
                offenders.append(f"{path.name}: os.environ access")
    assert offenders == [], offenders


# ---------------------------------------------------------------------------
# Field-level sweeps over the real dataclasses
# ---------------------------------------------------------------------------


def _all_dataclasses() -> list[type]:
    import importlib

    found: list[type] = []
    for path in MODULE_PATHS:
        if path.name == "__init__.py":
            continue
        module = importlib.import_module(f"epd2_document_service.{path.stem}")
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and is_dataclass(obj):
                found.append(obj)
    return found


def test_no_dataclass_carries_a_content_field() -> None:
    """The one exception, stated explicitly: `ContentDescriptor.digest` is
    a *digest*, and `DocumentVersion.content` is a `ContentDescriptor`,
    not bytes. No field anywhere holds a byte string."""
    offenders: list[str] = []
    for cls in _all_dataclasses():
        for field in fields(cls):
            if field.name in FORBIDDEN_CONTENT_KEYS and field.name != "content":
                offenders.append(f"{cls.__name__}.{field.name}")
            if "bytes" in str(field.type).lower():
                offenders.append(f"{cls.__name__}.{field.name}: {field.type}")
    assert offenders == [], offenders


def test_the_only_content_named_field_is_a_descriptor() -> None:
    from epd2_document_service.domain import ContentDescriptor
    from epd2_document_service.versions import DocumentVersion

    content_field = next(f for f in fields(DocumentVersion) if f.name == "content")
    assert "ContentDescriptor" in str(content_field.type)
    assert not any(f.name == "content" for f in fields(ContentDescriptor))


# ---------------------------------------------------------------------------
# Behavioural sweep over a full lifecycle
# ---------------------------------------------------------------------------


def _run_full_lifecycle() -> Fixture:
    """Exercise every command that emits an event, once."""
    from test_application import Flow  # noqa: PLC0415 - reuses the lifecycle driver

    flow = Flow()
    flow.to_published()
    app.issue_publication_rendition(
        flow.f.stores,
        context=flow.f.context(flow.f.publisher),
        port=flow.f.port,
        clock=clock_at(40),
        document_id=flow.document_id,
        version_number=1,
        rendition_id=uuid4(),
        rendition_content=b"<html>minutes</html>",
        media_type="text/html",
        reason=reason("DOCUMENT_RENDITION_ISSUED"),
    )
    app.determine_signature_status(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(41),
        document_id=flow.document_id,
        version_number=1,
        determination_id=uuid4(),
        status=SignatureStatus.SIGNED_VERIFIED,
        form=SignatureForm.QUALIFIED_ELECTRONIC,
        verification_basis_reference="validation-report-7",
        reason=reason("DOCUMENT_SIGNATURE_DETERMINED"),
    )
    app.bind_retention(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian),
        port=flow.f.port,
        clock=clock_at(42),
        document_id=flow.document_id,
        binding=retention_binding(),
        reason=reason("DOCUMENT_RETENTION_BOUND"),
    )
    evidence = app.register_evidence(
        flow.f.stores,
        context=flow.f.context(flow.f.evidence_custodian),
        port=flow.f.port,
        clock=clock_at(43),
        document_id=flow.document_id,
        version_number=1,
        evidence_id=uuid4(),
        matter_reference="case-2026-11",
        provenance=provenance(),
        holder_reference="registry-a",
        reason=reason("DOCUMENT_EVIDENCE_REGISTERED"),
    )
    app.seal_evidence_bundle(
        flow.f.stores,
        context=flow.f.context(flow.f.evidence_custodian),
        port=flow.f.port,
        clock=clock_at(44),
        bundle_id=uuid4(),
        matter_reference="case-2026-11",
        purpose_reference="hearing-bundle",
        evidence_ids=[evidence.evidence.evidence_id],
        reason=reason("DOCUMENT_EVIDENCE_BUNDLE_SEALED"),
    )
    return flow.f


def test_no_emitted_event_carries_content_identity_or_a_voting_linkage() -> None:
    """The broadest check in the suite: every payload a full lifecycle
    actually produces, re-run through the emission boundary."""
    fixture = _run_full_lifecycle()
    published = fixture.stores.sink.published()
    assert len(published) >= 10
    for envelope in published:
        assert_emission_safe(dict(envelope.payload), context=envelope.event_type)


def test_no_emitted_event_carries_the_actor_reference() -> None:
    """`actor_reference` is the closest thing this service holds to a
    per-actor handle, and an event stream carrying it would let every
    governed act be correlated to one person."""
    fixture = _run_full_lifecycle()
    actor_references = {
        fixture.custodian.actor_reference,
        fixture.author.actor_reference,
        fixture.reviewer.actor_reference,
        fixture.approver.actor_reference,
        fixture.publisher.actor_reference,
        fixture.evidence_custodian.actor_reference,
    }
    for envelope in fixture.stores.sink.published():
        rendered = str(dict(envelope.payload))
        for actor_reference in actor_references:
            assert actor_reference not in rendered, envelope.event_type


def test_no_emitted_event_carries_the_document_bytes() -> None:
    fixture = _run_full_lifecycle()
    for envelope in fixture.stores.sink.published():
        rendered = str(dict(envelope.payload))
        assert "minutes v1" not in rendered
        assert "<html>" not in rendered


def test_every_event_carries_its_organizational_scope() -> None:
    """FIR-INV-013: a consumer must always be able to tell which
    organization an event belongs to, without inferring it."""
    fixture = _run_full_lifecycle()
    for envelope in fixture.stores.sink.published():
        assert envelope.payload["organization_id"] == str(fixture.scope.organization_id)


def test_no_audit_row_carries_content_or_identity() -> None:
    """Audit metadata is a second surface, and PACK-09's own review found
    that a "full state" snapshot which silently omitted fields is the kind
    of gap nothing signals. The audit rows here carry hashes, not
    state."""
    fixture = _run_full_lifecycle()
    for row in fixture.stores.audit.list_all():
        rendered = str(row)
        assert "minutes v1" not in rendered
        for key in ("email", "full_name", "member_id"):
            assert key not in rendered


# ---------------------------------------------------------------------------
# The content read path
# ---------------------------------------------------------------------------


def test_content_leaves_only_through_the_authority_checked_read() -> None:
    """The one path by which content leaves this service - which is what
    lets every projection be content-free."""
    from test_application import Flow  # noqa: PLC0415

    flow = Flow()
    flow.to_approved()
    profile = AccessProfile(
        max_sensitivity=SensitivityClass.CONFIDENTIAL,
        scope=flow.f.scope,
        purpose_reference="governed-read",
    )
    payload = app.read_document_content(
        flow.f.stores,
        context=flow.f.context(flow.f.custodian, access_profile=profile),
        port=flow.f.port,
        document_id=flow.document_id,
        version_number=1,
    )
    assert payload == b"minutes v1"


def test_a_read_without_an_access_profile_denies() -> None:
    from test_application import Flow  # noqa: PLC0415

    flow = Flow()
    flow.to_approved()
    with pytest.raises(RestrictedAccessDeniedError):
        app.read_document_content(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian),
            port=flow.f.port,
            document_id=flow.document_id,
            version_number=1,
        )


def test_a_read_beyond_the_profile_ceiling_denies() -> None:
    from test_application import Flow  # noqa: PLC0415

    flow = Flow()
    flow.register(sensitivity=SensitivityClass.RESTRICTED)
    flow.record()
    profile = AccessProfile(
        max_sensitivity=SensitivityClass.INTERNAL,
        scope=flow.f.scope,
        purpose_reference="governed-read",
    )
    with pytest.raises(RestrictedAccessDeniedError):
        app.read_document_content(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian, access_profile=profile),
            port=flow.f.port,
            document_id=flow.document_id,
            version_number=1,
        )


def test_a_read_verifies_the_bytes_against_the_recorded_digest() -> None:
    """A caller never receives content this service cannot show is the
    content that was recorded."""
    from test_application import Flow  # noqa: PLC0415

    from epd2_document_service.exceptions import DocumentContentDigestMismatchError

    flow = Flow()
    flow.to_approved()
    version_record = flow.f.stores.versions.get_by_number(flow.document_id, 1)
    flow.f.stores.content._blobs[version_record.content.digest] = b"swapped"  # noqa: SLF001
    profile = AccessProfile(
        max_sensitivity=SensitivityClass.CONFIDENTIAL,
        scope=flow.f.scope,
        purpose_reference="governed-read",
    )
    with pytest.raises(DocumentContentDigestMismatchError):
        app.read_document_content(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian, access_profile=profile),
            port=flow.f.port,
            document_id=flow.document_id,
            version_number=1,
        )


def test_the_restricted_projection_path_is_authority_checked_too() -> None:
    from test_application import Flow  # noqa: PLC0415

    flow = Flow()
    flow.to_approved()
    with pytest.raises(RestrictedAccessDeniedError):
        app.restricted_projection(
            flow.f.stores,
            context=flow.f.context(flow.f.custodian),
            port=flow.f.port,
            clock=clock_at(50),
            document_id=flow.document_id,
            version_number=1,
        )


def test_an_independent_reader_may_read_and_is_re_verified_at_read_time() -> None:
    from test_application import Flow  # noqa: PLC0415

    from _builders import authority
    from epd2_document_service.authorization import DocumentRole
    from epd2_document_service.exceptions import AuditorIndependenceViolationError

    flow = Flow()
    flow.to_approved()
    profile = AccessProfile(
        max_sensitivity=SensitivityClass.CONFIDENTIAL,
        scope=flow.f.scope,
        purpose_reference="independent-audit",
    )
    projection = app.restricted_projection(
        flow.f.stores,
        context=flow.f.context(flow.f.independent_reader, access_profile=profile),
        port=flow.f.port,
        clock=clock_at(50),
        document_id=flow.document_id,
        version_number=1,
    )
    assert projection.is_authoritative is False

    compromised = authority(
        DocumentRole.INDEPENDENT_READER,
        flow.f.scope,
        flow.f.port,
        actor_reference="actor-lost-independence",
        also_holds=(DocumentRole.DOCUMENT_APPROVER,),
    )
    with pytest.raises((AuditorIndependenceViolationError, Exception)):
        app.restricted_projection(
            flow.f.stores,
            context=flow.f.context(compromised, access_profile=profile),
            port=flow.f.port,
            clock=clock_at(51),
            document_id=flow.document_id,
            version_number=1,
        )


# ---------------------------------------------------------------------------
# Declared status
# ---------------------------------------------------------------------------


def test_the_package_declares_a_reference_implementation_not_an_implementation() -> None:
    """`reference_implementation` is the truthful value: the governed
    workflow is real and the production data plane is PACK-13's."""
    assert epd2_document_service.DOCUMENT_CONTEXT_IMPLEMENTATION_STATUS == (
        "reference_implementation"
    )


def test_the_package_claims_only_the_two_fir_entries_it_fully_implements() -> None:
    """Foundation-only entries are deliberately absent: a foundation is
    not an implementation, and listing one here would be the false
    production claim FIR-INV-015 forbids."""
    assert epd2_document_service.IMPLEMENTED_FIR_ENTRIES == (
        "FIR-ROADMAP-001",
        "FIR-INV-010",
    )
