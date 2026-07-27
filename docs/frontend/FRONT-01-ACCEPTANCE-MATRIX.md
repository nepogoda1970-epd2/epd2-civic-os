# FRONT-01 Acceptance Matrix

| Requirement            | Evidence                                               | Gate      |
| ---------------------- | ------------------------------------------------------ | --------- |
| WS-01 only             | `data-workspace="WS-01"`, route and architecture tests | mandatory |
| Required public routes | 31 entries in route catalog and `publicPages`          | mandatory |
| Controlled maturity    | typed nine-value union and banner tests                | mandatory |
| No operational flows   | content/source negative assertions                     | mandatory |
| C1–C8                  | audit correction matrix and tests                      | mandatory |
| WC/FEC                 | audit correction matrix and migration map              | mandatory |
| Legacy completeness    | 61 migration rows, one per legacy HTML                 | mandatory |
| Accessibility          | axe, landmarks, skip link, keyboard and reduced motion | mandatory |
| Responsive UI          | 412, 1440 and 1920 Playwright projects                 | mandatory |
| Visual regression      | 30 committed FRONT-01 PNG baselines                    | mandatory |
| No broken links        | every internal link is crawled                         | mandatory |
| Versions               | repository scripts verify 0.9.0 / 0.7.0 unchanged      | mandatory |

Passing local gates makes the package an implementation candidate only.
