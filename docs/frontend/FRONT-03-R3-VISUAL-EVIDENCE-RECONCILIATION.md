# FRONT-03 R3 Visual Evidence Reconciliation

Status: governed R3 correction evidence
Stage: FRONT-03 — WS-02 Applicant & Member Core

## Conflict detected in entering R2 candidate

The exact entering R2 ZIP contains two mutually inconsistent visual/content states:

- the 27 stored FRONT-03 PNG files still show the pre-live-reconciliation presentation, including `Mitgliederbereich`, `WS 02 · MEMBER CORE`, `Mitgliedschaft`, `Initiativen`, `Beratung`, `Delegation`, and `Sicherheit`;
- the R2 executable `frontend/web-shell/member/MemberWorkspace.tsx` and R2 continuity documents already require the later public-product terminology and content continuity, including `Bürgerbereich`, `Profil & Mitgliedsstatus`, `Meine Vorschläge`, `Programmwerkstatt`, `Meine Stimmen & Delegation`, and cross-workspace continuity notices.

Entering R2 identities independently recalculated from the exact ZIP:

- `MemberWorkspace.tsx` SHA-256: `0c358d5b0685db2c0b1ca6be49e510dcf2aeb541576d231bf2b27e785b48eb0d`
- stored R2 FRONT-03 PNG count: `27`
- stored R2 FRONT-03 PNG set digest: `e0f9e67315f37ee30e63d712f4ce23b0e79008fcfed0eea38a403757ef2fc762`

The R3 correction assignment explicitly requires both:

1. preservation of the R2 live-site / legacy reconciliation improvements; and
2. fresh R3 browser/visual evidence after final source changes, without silently treating stale R2 results as current R3 evidence.

Reverting executable R3 content to the stored pre-reconciliation PNG wording would therefore regress an explicitly preserved R2 improvement and would violate the live-site continuity gate.

## Resolution

The stale R2 PNGs are retained as historical evidence and are not overwritten or represented as current R3 evidence.

R3 establishes a new immutable screenshot set from the final port-backed R3 implementation after all required live-site terminology, Applicant/Member boundaries, production fail-closed behavior, and scope-port wiring are present.

This is an **evidence reconciliation, not a visual redesign**:

- no new color system is authorized;
- no new typography system is authorized;
- no new radius system is authorized;
- no new spacing scale is authorized;
- no new navigation geometry is authorized as a design preference;
- no accepted FRONT-00 / FRONT-01 visual baseline may be changed;
- Member Core continues to use the governed existing EPD² shell/primitives and the R2 executable content model.

The visual difference relative to the stale R2 PNGs is caused by mandatory R2 live-site/content-continuity changes already present in the entering R2 executable source, not by an R3 designer-initiated restyle.

Accordingly the visual traceability status for these rows is `SECURITY_DRIVEN_BEHAVIOR_CHANGE_NO_RESTYLE` or `NEW_COMPONENT_FROM_EXISTING_PRIMITIVES`, not `GOVERNED_DESIGN_CHANGE_DECISION` and not `UNAPPROVED_REDESIGN`.

## Fail-closed verification rule

The canonical R3 PNG set is generated exactly once by CI and committed together with a SHA-256 manifest. That bootstrap run is not permitted to become PASS.

Every subsequent final verification run must:

1. start from the committed canonical R3 PNG/manifest set;
2. delete the working screenshot directory;
3. regenerate all 27 screenshots from the final R3 source;
4. compare every regenerated PNG against the committed SHA-256 manifest;
5. fail if any PNG is missing, unexpected, or differs by even one byte.

The final evidence therefore cannot become GREEN merely by overwriting screenshots during the verification run.
