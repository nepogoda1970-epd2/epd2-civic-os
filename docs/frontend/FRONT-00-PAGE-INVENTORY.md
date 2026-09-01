# FRONT-00 Existing Page Inventory

The complete mechanical inventory is `FRONT-00-PAGE-INVENTORY.csv`. It records
every file from `EPD_Front.zip` with title, template, shared elements/CSS,
target workspace/route, migration status, preservation decision and technical
correction. Only these representative pages are migrated:

| Source                       | Fixture         | Type               | Status                                      |
| ---------------------------- | --------------- | ------------------ | ------------------------------------------- |
| `index.html`                 | `public`        | public             | representative migration                    |
| `intern/dashboard.html`      | `cockpit`       | dashboard          | representative migration                    |
| `intern/kommunikation.html`  | `communication` | structured content | representative migration                    |
| `buerger-login.html`         | `form`          | form-oriented      | representative migration; no authentication |
| `struktur/abstimmungen.html` | `table`         | list/table         | representative migration; no voting         |

All other pages remain preserved source references and are not mass-migrated.
