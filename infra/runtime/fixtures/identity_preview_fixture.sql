-- EPD2 INFRA-03 deterministic preview fixture (assignment §34).
--
-- Synthetic, deterministic, clearly-marked preview data for the identity
-- database, inserted through the canonical schema only. No production or
-- member/person data ever appears here; the account ids are fixture
-- namespaced and the reset proof asserts they are fully gone after reset.

INSERT INTO account_registry_record
    (account_id, account_status, scope_level, scope_unit_id, created_at,
     anonymization_state, version, document)
VALUES
    ('preview-fixture-0001', 'active', 'federal', 'preview-unit-01',
     '2026-01-01T00:00:00+00:00', 'none', 1, '{"fixture": true}'),
    ('preview-fixture-0002', 'active', 'federal', 'preview-unit-01',
     '2026-01-01T00:00:00+00:00', 'none', 1, '{"fixture": true}'),
    ('preview-fixture-0003', 'pending', 'land', 'preview-unit-02',
     '2026-01-01T00:00:00+00:00', 'none', 1, '{"fixture": true}')
ON CONFLICT (account_id) DO NOTHING;
