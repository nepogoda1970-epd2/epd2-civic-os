# Contributing to EPD² Civic OS

## Workflow

- All changes are made through a Pull Request. Direct pushes to `main` are
  not permitted; `main` is protected and only receives changes via reviewed
  and merged Pull Requests.
- Every Pull Request must pass all required checks (`make verify` locally,
  and the CI workflow in `.github/workflows/ci.yml`) before it can be merged.
- Every Pull Request must use the template in
  `.github/pull_request_template.md`.

## Tests

- Tests are mandatory for any change that adds or modifies behavior.
- A Pull Request that reduces test coverage of an existing guarantee without
  justification will not be merged.
- Run `make test` (or the more targeted `make test-python`,
  `make test-typescript`, `make test-frontend`) before opening a Pull
  Request.

## Changing the canon

- The canonical domain and event model
  (`docs/canonical/TZ-00-domain-event-canon.md`) is **not** editable as part
  of routine feature work.
- Any change to canonical entities, statuses, transitions, events, reason
  codes, or architectural invariants requires a dedicated
  `Architecture Decision Record` (ADR) under `docs/adr/`, using the template
  in `docs/adr/ADR-000-template.md`.
- A canon change is not implemented in working code until its ADR reaches
  status `accepted`.
- Use the `architecture_change.yml` issue template
  (`.github/ISSUE_TEMPLATE/architecture_change.yml`) to propose such changes.

## Changing shared contracts

- Shared contracts under `contracts/` (OpenAPI specs, event schemas, JSON
  schemas, reason codes) are shared surface area for multiple modules.
- Any change to a shared contract must be versioned. Breaking changes
  require a new major version and must not silently replace the previous
  version's meaning.
- Consumers must be able to detect and reject an unsupported contract
  version (fail-closed), per `INV-10` of the canon.

## Commit messages

- Write commit messages in the imperative mood ("Add", "Fix", "Update"), one
  concise summary line, followed by an optional body explaining the "why"
  when it is not obvious.
- Reference the related package, issue, or ADR where relevant.

## Documentation requirements

- Any new module, package, or service must include a `README.md` describing
  its purpose, ownership, and boundaries.
- Any open question or ambiguity encountered during implementation must be
  recorded in `docs/review/OPEN_QUESTIONS.md` rather than resolved
  unilaterally.
- Any known limitation of the current state of the repository must be kept
  up to date in `docs/review/KNOWN_LIMITATIONS.md`.
