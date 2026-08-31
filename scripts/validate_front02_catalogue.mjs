import { readFileSync } from "node:fs";

const file = new URL(
  "../docs/frontend/FRONT-02-PAGE-CATALOGUE.csv",
  import.meta.url,
);
const [header, ...rows] = readFileSync(file, "utf8").trim().split("\n");
const required = [
  "id",
  "path",
  "workspace",
  "kind",
  "visibility",
  "status",
  "authority",
  "scope",
  "dependency",
  "locale",
  "fixture",
];
if (
  header.split(",").length !== required.length ||
  required.some((name) => !header.split(",").includes(name))
)
  throw new Error("catalogue header is incomplete");
const paths = new Set();
for (const row of rows) {
  const values = row.split(",");
  if (values.length !== required.length || values.some((value) => !value))
    throw new Error(`invalid catalogue row: ${row}`);
  if (!values[1].startsWith("/") || paths.has(values[1]))
    throw new Error(`invalid or duplicate path: ${values[1]}`);
  if (values[2] !== "WS-01")
    throw new Error(`public catalogue must stay in WS-01: ${values[2]}`);
  paths.add(values[1]);
}
for (const path of [
  "/aktuelles",
  "/presse",
  "/termine",
  "/regionen",
  "/personen",
  "/wahlen",
  "/hilfe",
  "/suche",
])
  if (!paths.has(path)) throw new Error(`missing governed route ${path}`);
console.log(`FRONT-02 catalogue valid: ${rows.length} entries`);
