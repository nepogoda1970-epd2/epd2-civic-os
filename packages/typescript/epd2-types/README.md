# epd2-types

Shared TypeScript package for EPD² Civic OS. Contains no domain types on
this stage — only version constants, mirroring
`packages/python/epd2-core`.

## Contents

- `CANON_VERSION` — the canon version this repository targets
  (see `docs/canonical/canon-version.json`).
- `REPOSITORY_VERSION` — the repository skeleton version.

## Usage

```ts
import { CANON_VERSION, REPOSITORY_VERSION } from "epd2-types";
```

## Boundaries

This package does not duplicate the Python UUID generation logic from
`epd2-core`, and does not define any domain entity types. It exists purely
as a shared, version-consistency anchor for future TypeScript consumers
(e.g. the frontend).
