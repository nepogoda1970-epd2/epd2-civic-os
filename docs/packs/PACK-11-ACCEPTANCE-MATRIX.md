# PACK-11 — acceptance matrix

Every acceptance criterion this round claims, and the executable evidence
for it. A criterion with no test is not a criterion.

## Objective (task section 1)

| Requirement                                   | Evidence                                                                                                                                                                                                                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| organization-scoped document ownership        | `test_domain.py::test_a_foreign_scope_is_refused`, `test_application.py::test_a_foreign_document_is_reported_exactly_as_a_missing_one`, `test_storage.py::test_listing_documents_filters_by_scope`                                                                 |
| immutable document versions                   | `test_versions.py::test_a_rewritten_version_breaks_the_chain_at_that_version`, `test_storage.py::test_a_stored_version_is_never_replaced`, `::test_a_state_change_may_not_alter_anything_the_hash_covers`                                                          |
| cryptographically linked version history      | `test_versions.py` (34 tests), especially `::test_a_removed_version_breaks_the_chain`, `::test_a_reparented_version_breaks_the_chain`, `::test_a_resealed_forgery_still_breaks_the_chain_downstream`                                                               |
| typed document and evidence references        | `test_references.py::test_no_outward_reference_carries_content_or_an_assertion`, `::test_reference_types_are_not_interchangeable`, `::test_every_outward_reference_carries_its_scope`                                                                              |
| controlled review and approval                | `test_documents.py::test_approval_requires_every_mandated_review_kind`, `::test_approval_refuses_while_a_blocking_finding_is_open`, `test_application.py::test_a_review_may_only_be_recorded_on_a_version_in_review`                                               |
| publication lifecycle                         | `test_documents.py::test_publication_requires_its_own_authorization`, `test_application.py::test_publication_requires_its_own_authorization`, `::test_a_rendition_requires_a_published_version`                                                                    |
| restricted and public projections             | `test_projections.py` (20 tests)                                                                                                                                                                                                                                   |
| correction, supersession and revocation       | `test_versions.py::test_a_correction_does_not_alter_the_corrected_version`, `test_application.py::test_supersession_moves_the_current_version_pointer`, `::test_revocation_removes_effect_and_keeps_the_record`                                                    |
| legal hold                                    | `test_documents.py::test_an_active_hold_blocks_destruction`, `::test_an_indeterminate_hold_fails_closed_with_its_own_code`, `test_application.py::test_disposition_is_refused_under_an_active_hold`, `::test_disposition_fails_closed_under_an_indeterminate_hold` |
| retention metadata                            | `test_domain.py::test_a_retention_binding_requires_both_pack_09_references`, `test_application.py::test_disposition_without_a_retention_binding_is_refused`                                                                                                        |
| evidence bundles                              | `test_evidence.py` (bundle section), `test_application.py::test_a_sealed_bundle_is_citable_and_immutable`                                                                                                                                                          |
| provenance                                    | `test_domain.py::test_ai_generated_material_requires_an_analysis_provenance_reference`, `test_versions.py::test_the_hash_covers_provenance`                                                                                                                        |
| complete audit history                        | `test_application.py::test_audit_is_appended_before_the_event_is_published`, `::test_every_command_leaves_an_audit_row_and_one_event`                                                                                                                              |
| scoped authorization and separation of duties | `test_authorization.py` (31 tests), `test_application.py` separation section                                                                                                                                                                                       |

## ADR-053's four interface requirements

| #   | Requirement                                                       | Evidence                                                                                                                                                                         |
| --- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | resolve a reference to existence and kind within a scope          | `test_application.py::test_resolution_reports_existence_and_kind_in_scope`, `::test_resolution_across_scopes_reports_the_same_answer_as_a_missing_document`                      |
| 2   | report signature status as a governed determination, not inferred | `test_determinations.py::test_an_absent_signature_determination_is_a_reason_coded_refusal`, `test_application.py::test_an_absent_signature_determination_reports_not_determined` |
| 3   | report an admissibility determination                             | `test_application.py::test_an_admissibility_answer_is_scoped_to_its_procedure`, `test_determinations.py::test_an_admission_in_one_procedure_says_nothing_about_another`          |
| 4   | produce a citable publication rendition identifier                | `test_application.py::test_a_rendition_citation_resolves_the_version_it_renders`, `test_documents.py::test_a_rendition_citation_carries_no_content`                              |

## Hard invariants

| Invariant                                      | Evidence                                                                                                                                                                                                                |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-INV-001` no global user ID                | `test_privacy_boundary.py::test_the_package_defines_no_identity_field_anywhere`, `::test_no_emitted_event_carries_the_actor_reference`, `test_domain.py::test_every_prohibited_identity_key_is_caught_at_the_top_level` |
| `FIR-INV-002` / `FIR-INV-003` voting isolation | `test_privacy_boundary.py::test_the_package_declares_no_voting_field_anywhere`, `test_events.py::test_a_voting_linkage_cannot_reach_an_event`                                                                           |
| `FIR-INV-006` safe feature flags               | `test_privacy_boundary.py::test_no_module_offers_a_break_glass_switch`, `test_authorization.py::test_the_no_break_glass_rule_is_stated_as_a_quotable_constant`                                                          |
| `FIR-INV-010` version integrity                | the whole of `test_versions.py`, plus `test_application.py::test_a_command_refuses_to_act_on_a_document_whose_history_is_broken`                                                                                        |
| `FIR-INV-013` scope isolation                  | `test_privacy_boundary.py::test_every_event_carries_its_organizational_scope`, `test_authorization.py::test_an_authority_in_another_scope_is_not_considered`                                                            |
| `FIR-INV-014` no universal administration      | `test_authorization.py::test_every_action_has_a_requirement_entry` plus the eight-role decomposition; no action accepts "any authority"                                                                                 |
| `FIR-INV-015` no false production claims       | `test_privacy_boundary.py::test_the_package_declares_a_reference_implementation_not_an_implementation`, `::test_the_package_claims_only_the_two_fir_entries_it_fully_implements`                                        |

## Contract tests (canon section 27)

| CT                                 | Applied as                                                                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| CT-00-02 Unknown Status            | `test_versions.py::test_an_unknown_state_is_refused`, `test_documents.py::test_an_unknown_document_state_is_refused`           |
| CT-00-03 Forbidden Transition      | `test_versions.py::test_a_draft_cannot_be_published_without_review_and_approval`                                               |
| CT-00-04 Event Idempotency         | `test_application.py::test_a_replayed_command_does_not_act_twice`, `::test_the_same_event_id_with_different_content_conflicts` |
| CT-00-05 Unsupported Event Version | `test_events.py::test_an_unknown_major_version_is_not_processed`                                                               |
| CT-00-06 Missing Permission        | `test_application.py::test_a_wrong_role_denies`                                                                                |
| CT-00-07 Audit Creation            | `test_application.py::test_every_command_leaves_an_audit_row_and_one_event`                                                    |
| CT-00-08 Identity Leakage          | `test_privacy_boundary.py::test_no_emitted_event_carries_content_identity_or_a_voting_linkage`                                 |
| CT-00-09 Vote Linkability          | `test_events.py::test_a_voting_linkage_cannot_reach_an_event`                                                                  |

## Repository-level

| Requirement                                       | Evidence                                                                                              |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| document-service imports only the shared packages | `tests/repository/test_service_boundaries.py::test_document_service_imports_only_core_and_audit_core` |
| nothing imports document-service                  | `::test_no_other_service_imports_document_service`                                                    |
| no delete-shaped storage method                   | `::test_document_service_storage_exposes_no_delete_operation`                                         |
| no declared dependency on another service         | `::test_document_service_declares_no_dependency_on_another_service_package`                           |
| the context is declared and has a runtime         | `scripts/check_canon_0_8_0.py::check_document_implementation_status`                                  |
| reason codes registered and complete              | `tests/contract/test_reason_codes_registry.py` (`pack-11` row, ≥ 71)                                  |

## Not claimed

Legal validity, evidential admissibility, signature verification,
qualified-electronic-signature conformance, production readiness, tamper
_resistance_, and any assertion about German party law. See
`docs/handover/PACK-11-KNOWN-LIMITATIONS.md`.
