# FRONT-01 Visual Baselines

Thirty committed Playwright PNG baselines cover ten representative pages at
412 px mobile, 1440 px desktop and 1920 px wide:

1. homepage;
2. about/goals;
3. open program structure;
4. program section detail;
5. initiative lifecycle;
6. voting explanation;
7. transparency model;
8. technology/security;
9. participation;
10. roadmap/status.

CI runs normal comparison mode through `make verify`. Snapshot update mode is
never used in CI. The candidate banner is the only masked area because its
handover label may change without altering page semantics.
