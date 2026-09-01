# FRONT-00 Component Catalog

| Component or native pattern        | Purpose                                               | Test evidence      |
| ---------------------------------- | ----------------------------------------------------- | ------------------ |
| `WorkspaceShell`                   | workspace landmarks, skip link, navigation            | rendered + browser |
| `Button`                           | primary, secondary, quiet, destructive, disabled      | rendered           |
| `LinkButton`                       | navigation styled as an action                        | showcase + browser |
| `StatusBadge`                      | typed text-and-marker status                          | rendered + axe     |
| `Breadcrumb` / `BackLink`          | hierarchy and return navigation                       | rendered           |
| `SecondaryNavigation` / `Tabs`     | sibling sections and current state                    | rendered           |
| `Card` / `MetricCard`              | content and metric grouping                           | browser            |
| `Notice`                           | information, warning, danger, authority, scope, legal | showcase + axe     |
| `RestrictedContentNotice`          | authority-gated content explanation                   | showcase           |
| `StaleDataWarning`                 | stale/unknown data warning                            | showcase           |
| `StatePanel`                       | all 19 presentation states and live status            | rendered           |
| `MetadataList`                     | semantic definition/metadata list                     | showcase + axe     |
| `StructuredList`                   | structured list                                       | showcase + axe     |
| `AccessibleTableContainer`         | labelled, keyboard-focusable horizontal scrolling     | browser + axe      |
| `SearchField`                      | labelled search input                                 | browser + axe      |
| `FilterGroup`                      | fieldset/legend filter grouping                       | showcase + axe     |
| `ProvenancePanel`                  | source/version/correction path                        | rendered           |
| `Pagination`                       | current page and disabled boundaries                  | rendered           |
| `DialogExample`                    | confirmation, cancel, focus movement/return           | rendered + browser |
| Native `input`/`textarea`/`select` | ordinary labelled controls                            | showcase + axe     |
| Native checkbox/radio/fieldset     | grouped binary/single-choice controls                 | showcase + axe     |
| Native `input[type=date]`          | date input wrapper is label + `FormField`             | showcase + axe     |

`FormField` owns label, hint, and error IDs. The input intentionally remains
native and explicitly supplies `aria-describedby="<id>-hint <id>-error"` when
both are present. Validation uses a visible `role=alert` message. This explicit
native pattern avoids wrappers that obscure HTML behavior.

All patterns are documentation fixtures. They do not assert authorization,
business validity, backend state, or legal activation.

For a future Mobile App, only design tokens, schemas, generated API types,
accessibility patterns, and non-authoritative UI components may be reused.
Runtime authority/session/voting state is explicitly outside this catalogue.
