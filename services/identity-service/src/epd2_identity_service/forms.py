"""Forms and governed content as **assets**, not strings at call sites.

`PACK-14-FORM-INVENTORY.md` names fifteen forms and
`PACK-14-CONTENT-CATALOGUE-DE.md` carries their real German texts,
versioned `P14-DE-1.0.0`. This module makes both machine-readable and
testable: a form is a value with an ID, a version, an authentication
class, a workflow and a retention class, and its consequential texts are
looked up from `GOVERNED_CONTENT` rather than written into a template.

The rule that makes this worth doing: **frontend developers must not
invent missing process logic or consequential content.** A label that
appears in a UI and not in the catalogue is a decision somebody made
without governance, and `assert_governed_text()` turns that into a test
failure rather than a production surprise.

The catalogue's own closing principle is enforced structurally by
`RefusalText`, which has no way to be constructed without all three
parts:

> Jede Ablehnung nennt einen Grund, die zuständige Stelle und den
> nächsten möglichen Schritt.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import UnknownFormIdError

#: The content catalogue's own version, from its header table. Bound to
#: form version 1 for every form below (`FIR-FORM-004`).
CONTENT_VERSION = "P14-DE-1.0.0"
CONTENT_LANGUAGE = "de"
FORM_VERSION = 1

#: **Not yet in force.** The catalogue's "effective from" is the
#: acceptance of the implementation round, and this round is a candidate.
CONTENT_IN_FORCE = False


class ConfidentialityClass(StrEnum):
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True, slots=True)
class FormDefinition:
    """One row of the form inventory, as data.

    `form_id` is **provisional** until `FIR-FORM-001`'s canonical forms
    framework exists and assigns real ones - recorded here so the
    provisionality travels with the value rather than living only in a
    document.
    """

    form_id: str
    name_de: str
    receiving_authority: str
    basis: str
    confidentiality: ConfidentialityClass
    required_assurance: AuthenticationAssuranceLevel
    step_up_required: bool
    workflow: tuple[str, ...]
    retention_class: str
    provisional: bool = True

    def __post_init__(self) -> None:
        if not self.workflow:
            raise ValueError("a form definition names its workflow steps")


FORMS: dict[str, FormDefinition] = {
    "F-P14-01": FormDefinition(
        form_id="F-P14-01",
        name_de="Kontoregistrierung",
        receiving_authority="Account Registry",
        basis="Platform terms; FIR-ROADMAP-004",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.NONE,
        step_up_required=False,
        workflow=("submit", "verify_contact", "activate"),
        retention_class="account_record",
    ),
    "F-P14-02": FormDefinition(
        form_id="F-P14-02",
        name_de="E-Mail-Bestätigung",
        receiving_authority="Account Registry",
        basis="Platform terms",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.LOW,
        step_up_required=False,
        workflow=("request", "confirm"),
        retention_class="contact_history",
    ),
    "F-P14-03": FormDefinition(
        form_id="F-P14-03",
        name_de="Telefonnummer-Bestätigung",
        receiving_authority="Account Registry",
        basis="Platform terms",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.LOW,
        step_up_required=False,
        workflow=("request", "confirm"),
        retention_class="contact_history",
    ),
    "F-P14-04": FormDefinition(
        form_id="F-P14-04",
        name_de="Passkey einrichten",
        receiving_authority="Authentication",
        basis="ADR-081",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        step_up_required=True,
        workflow=("initiate", "attest", "name", "confirm"),
        retention_class="credential_metadata",
    ),
    "F-P14-05": FormDefinition(
        form_id="F-P14-05",
        name_de="Passkey entfernen",
        receiving_authority="Authentication",
        basis="ADR-081",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.HIGH,
        step_up_required=True,
        workflow=("select", "confirm_consequences", "remove"),
        retention_class="credential_metadata",
    ),
    "F-P14-06": FormDefinition(
        form_id="F-P14-06",
        name_de="Zwei-Faktor-Verfahren einrichten",
        receiving_authority="Authentication",
        basis="ADR-082",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        step_up_required=True,
        workflow=("choose", "enroll", "verify", "confirm"),
        retention_class="credential_metadata",
    ),
    "F-P14-07": FormDefinition(
        form_id="F-P14-07",
        name_de="Zwei-Faktor-Verfahren entfernen",
        receiving_authority="Authentication",
        basis="ADR-082",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        step_up_required=True,
        workflow=("select", "confirm_downgrade", "remove"),
        retention_class="credential_metadata",
    ),
    "F-P14-08": FormDefinition(
        form_id="F-P14-08",
        name_de="Wiederherstellungscodes erzeugen",
        receiving_authority="Authentication",
        basis="ADR-085",
        confidentiality=ConfidentialityClass.CONFIDENTIAL,
        required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        step_up_required=True,
        workflow=("request", "display_once", "confirm_stored"),
        retention_class="credential_metadata",
    ),
    "F-P14-09": FormDefinition(
        form_id="F-P14-09",
        name_de="Kontowiederherstellung beantragen",
        receiving_authority="Recovery",
        basis="ADR-085",
        confidentiality=ConfidentialityClass.CONFIDENTIAL,
        required_assurance=AuthenticationAssuranceLevel.NONE,
        step_up_required=False,
        workflow=("request", "assess", "verify", "cooling_off", "complete"),
        retention_class="recovery_evidence",
    ),
    "F-P14-10": FormDefinition(
        form_id="F-P14-10",
        name_de="Verdächtige Anmeldung bestätigen oder melden",
        receiving_authority="Session Security",
        basis="ADR-083",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.LOW,
        step_up_required=False,
        workflow=("notify", "confirm_or_report", "respond"),
        retention_class="suspicious_activity",
    ),
    "F-P14-11": FormDefinition(
        form_id="F-P14-11",
        name_de="Kontaktdaten ändern",
        receiving_authority="Account Registry",
        basis="ADR-084",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        step_up_required=True,
        workflow=("request", "verify_new", "notify_both", "apply"),
        retention_class="contact_history",
    ),
    "F-P14-12": FormDefinition(
        form_id="F-P14-12",
        name_de="Aktive Sitzungen beenden",
        receiving_authority="Session Security",
        basis="ADR-083",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        step_up_required=True,
        workflow=("list", "select", "confirm", "revoke"),
        retention_class="session_history",
    ),
    "F-P14-13": FormDefinition(
        form_id="F-P14-13",
        name_de="Konto schließen",
        receiving_authority="Account Registry",
        basis="ADR-084",
        confidentiality=ConfidentialityClass.INTERNAL,
        required_assurance=AuthenticationAssuranceLevel.HIGH,
        step_up_required=True,
        workflow=("request", "cooling_off", "close", "retain_or_anonymize"),
        retention_class="account_record",
    ),
    "F-P14-14": FormDefinition(
        form_id="F-P14-14",
        name_de="Identitätsprüfung einreichen",
        receiving_authority="Identity Proofing",
        basis="ADR-086; canon 19d.2",
        confidentiality=ConfidentialityClass.RESTRICTED,
        required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        step_up_required=True,
        workflow=("submit", "evidence", "decide_or_review"),
        retention_class="proofing_evidence",
    ),
    "F-P14-15": FormDefinition(
        form_id="F-P14-15",
        name_de="Privilegierte Wiederherstellung genehmigen",
        receiving_authority="Identity Administration",
        basis="ADR-085, ADR-087",
        confidentiality=ConfidentialityClass.RESTRICTED,
        required_assurance=AuthenticationAssuranceLevel.HIGH,
        step_up_required=True,
        workflow=("assess", "dual_control", "decide"),
        retention_class="privileged_action",
    ),
}


def form(form_id: str) -> FormDefinition:
    try:
        return FORMS[form_id]
    except KeyError as exc:
        raise UnknownFormIdError(f"unknown PACK-14 form id: {form_id!r}") from exc


@dataclass(frozen=True, slots=True)
class RefusalText:
    """The catalogue's closing principle, as a type.

    All three parts are required fields, so a refusal message without a
    responsible body or a next step cannot be constructed. "Eine
    Ablehnung ohne Weg nach vorn ist in diesem System kein zulässiger
    Text" is therefore something the code enforces rather than something
    a reviewer has to notice.
    """

    reason_de: str
    responsible_body_de: str
    next_step_de: str

    def __post_init__(self) -> None:
        for name in ("reason_de", "responsible_body_de", "next_step_de"):
            if not getattr(self, name).strip():
                raise ValueError(
                    "jede Ablehnung nennt einen Grund, die zuständige Stelle und den "
                    "nächsten möglichen Schritt"
                )

    def render(self) -> str:
        return f"{self.reason_de} {self.responsible_body_de} {self.next_step_de}"


#: The recurring building blocks from catalogue §15, verbatim. Keyed by
#: the reason code they accompany, so a refusal surfaced to a person is
#: looked up from the governed text rather than composed at the call
#: site.
GOVERNED_CONTENT: dict[str, str] = {
    "STEP_UP_REQUIRED": (
        "Für diesen Schritt ist eine erneute Bestätigung Ihrer Identität erforderlich."
    ),
    "STEP_UP_EXPIRED": "Ihre Bestätigung ist abgelaufen. Bitte bestätigen Sie erneut.",
    "STEP_UP_OBJECT_CHANGED": (
        "Der Vorgang hat sich geändert, nachdem Sie ihn bestätigt haben. "
        "Bitte prüfen Sie die Änderung und bestätigen Sie erneut."
    ),
    "ASSURANCE_INSUFFICIENT": ("Für diese Handlung ist ein höheres Schutzniveau erforderlich."),
    "SESSION_EXPIRED": "Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.",
    "SESSION_REVOKED": ("Diese Sitzung wurde beendet und kann nicht fortgesetzt werden."),
    "EXTERNAL_PROVIDER_UNAVAILABLE": (
        "Der Dienst ist derzeit nicht erreichbar. Aus Sicherheitsgründen wird diese "
        "Handlung nicht ausgeführt. Bitte versuchen Sie es später erneut."
    ),
    "ACCOUNT_LOCKED": (
        "Ihr Konto ist derzeit gesperrt ({reason_code}). Die Mitteilung nennt Ihnen die "
        "zuständige Stelle und den Weg zum Widerspruch."
    ),
    "CREDENTIAL_LAST_REMAINING": (
        "Dies ist Ihr einziges Anmeldeverfahren. Es kann nicht entfernt werden, solange "
        "kein zweiter Zugang oder ein eingerichteter Wiederherstellungsweg besteht. "
        "Richten Sie zuerst einen weiteren Passkey oder Wiederherstellungscodes ein."
    ),
    "RECOVERY_CONTACT_RECENTLY_CHANGED": (
        "Dieser Kontaktweg wurde vor Kurzem geändert und kann derzeit nicht als "
        "alleiniger Nachweis dienen. Bitte wählen Sie einen anderen Weg oder wenden Sie "
        "sich an die Unterstützung."
    ),
    "RECOVERY_SELF_APPROVAL_REFUSED": (
        "Diese Entscheidung ist nicht zulässig, da Sie den Vorgang eingeleitet haben "
        "oder betroffen sind."
    ),
    "IDENTITY_PROOFING_INCONCLUSIVE": (
        "Ihre Angaben konnten nicht abschließend geprüft werden. Der Vorgang wurde zur "
        "manuellen Prüfung weitergeleitet."
    ),
    "CONTACT_ALREADY_IN_USE": (
        "Wenn zu dieser Adresse ein Konto besteht, erhalten Sie eine Nachricht."
    ),
    "CREDENTIAL_INVALID": (
        "Wenn zu dieser Adresse ein Konto besteht, erhalten Sie eine Nachricht."
    ),
}

#: The account-closure notice that must appear on `F-P14-13`, because the
#: single most consequential misunderstanding in this whole pack is a
#: member believing that closing an account resigns their membership.
CLOSURE_MEMBERSHIP_NOTICE_DE = (
    "Das Schließen des Kontos beendet nicht Ihre Mitgliedschaft. Ein Austritt aus der "
    "Partei ist ein eigenes Verfahren."
)

#: The proofing notice carrying canon 19d.2's prohibition in the words a
#: person actually reads.
PROOFING_NOTICE_DE = (
    "Ein Identitätsnachweis ist keine Aussage über Ihre Staatsangehörigkeit und keine "
    "Entscheidung über eine Mitgliedschaft."
)

#: The submission receipt's closing sentence (catalogue §14).
RECEIPT_CLOSING_DE = (
    "Diese Bestätigung dokumentiert den Eingang. Sie ist keine Entscheidung in der Sache."
)


def governed_text(reason_code: str) -> str:
    """Look up the governed text for a reason code.

    Raises rather than falling back to the code itself: a missing text is
    a governance gap, and printing a machine code at a person is how a
    gap gets shipped.
    """
    try:
        return GOVERNED_CONTENT[reason_code]
    except KeyError as exc:
        raise UnknownFormIdError(
            f"no governed German text is registered for reason code {reason_code!r}; "
            "consequential content is never invented at a call site"
        ) from exc


def assert_governed_text(text: str) -> None:
    """Assert a consequential label came from the catalogue.

    Used by tests over the reference UI surfaces. It is deliberately an
    exact-membership check: paraphrasing a governed text is the same
    governance failure as inventing one.
    """
    known = set(GOVERNED_CONTENT.values()) | {
        CLOSURE_MEMBERSHIP_NOTICE_DE,
        PROOFING_NOTICE_DE,
        RECEIPT_CLOSING_DE,
    }
    if text not in known:
        raise UnknownFormIdError(
            "this consequential text is not in PACK-14-CONTENT-CATALOGUE-DE.md; "
            "governed content is not invented at a call site"
        )
