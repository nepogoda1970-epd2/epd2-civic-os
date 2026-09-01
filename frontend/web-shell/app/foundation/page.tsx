import Link from "next/link";

import { DialogExample } from "../../components/DialogExample";
import {
  AccessibleTableContainer,
  BackLink,
  Button,
  Card,
  FilterGroup,
  FormField,
  LinkButton,
  MetadataList,
  Notice,
  PageHeader,
  Pagination,
  ProvenancePanel,
  RestrictedContentNotice,
  SearchField,
  SecondaryNavigation,
  StaleDataWarning,
  StatePanel,
  StatusBadge,
  StructuredList,
  Tabs,
  WorkspaceShell,
} from "../../components/foundation";
import { PRESENTATION_STATES } from "../../foundation/types";
import { WORKSPACES } from "../../foundation/workspaces";

export default function FoundationPage() {
  return (
    <WorkspaceShell workspaceId="WS-01">
      <PageHeader
        description="Nicht-produktive Dokumentation der gemeinsamen UI-Grundlage."
        title="Frontend Foundation"
      />
      <div className="grid">
        <Card title="Workspaces">
          <p>
            {WORKSPACES.length} getrennte Origin- und Sicherheitskontexte sind
            deklariert.
          </p>
        </Card>
        <Card title="Zustände">
          <p>
            {PRESENTATION_STATES.length} wiederverwendbare
            Präsentationszustände.
          </p>
        </Card>
      </div>
      <section className="section-block">
        <h2>Migrierte repräsentative Fixtures</h2>
        <ul className="structured-list">
          {["public", "cockpit", "communication", "form", "table"].map(
            (fixture) => (
              <li key={fixture}>
                <Link href={`/foundation/examples/${fixture}`}>{fixture}</Link>
              </li>
            ),
          )}
        </ul>
      </section>
      <section className="section-block">
        <h2>Komponentenkatalog</h2>
        <SecondaryNavigation
          label="Sekundärnavigation"
          items={[
            { href: "#actions", label: "Aktionen", current: true },
            { href: "#forms", label: "Formulare" },
            { href: "#data", label: "Daten" },
          ]}
        />
        <div className="grid" id="actions">
          <Card title="Aktionen und Status">
            <div className="fixture-actions">
              <Button>Primär</Button>
              <Button variant="secondary">Sekundär</Button>
              <Button variant="quiet">Leise</Button>
              <Button variant="destructive">Destruktiv</Button>
              <Button disabled>Deaktiviert</Button>
              <LinkButton href="#forms">Link als Button</LinkButton>
            </div>
            <p>
              <StatusBadge state="under_review">In Prüfung</StatusBadge>
            </p>
            <BackLink href="/">Zurück</BackLink>
          </Card>
          <Card title="Hinweise">
            <Notice title="Information">Sachlicher Hinweis.</Notice>
            <StaleDataWarning>Stand: unbekannt.</StaleDataWarning>
            <RestrictedContentNotice>
              Autorisierung erforderlich.
            </RestrictedContentNotice>
          </Card>
        </div>
        <Card title="Formularmuster">
          <form className="form-example" id="forms">
            <FormField
              id="showcase-text"
              label="Text"
              hint="Hilfetext"
              error="Beispiel-Validierung"
            >
              <input
                aria-describedby="showcase-text-hint showcase-text-error"
                id="showcase-text"
              />
            </FormField>
            <FormField id="showcase-textarea" label="Mehrzeiliger Text">
              <textarea id="showcase-textarea" />
            </FormField>
            <FormField id="showcase-select" label="Auswahl">
              <select id="showcase-select">
                <option>Bitte wählen</option>
              </select>
            </FormField>
            <FormField id="showcase-date" label="Datum">
              <input id="showcase-date" type="date" />
            </FormField>
            <SearchField
              id="showcase-search"
              label="Katalog durchsuchen"
              placeholder="Suchen"
            />
            <FilterGroup legend="Filter">
              <label>
                <input name="showcase-check" type="checkbox" /> Aktiv
              </label>
              <label>
                <input name="showcase-radio" type="radio" /> Neu
              </label>
              <label>
                <input name="showcase-radio" type="radio" /> Archiviert
              </label>
            </FilterGroup>
          </form>
          <DialogExample />
        </Card>
        <Card title="Navigation, Metadaten und Tabelle">
          <Tabs
            items={[
              { href: "#data", label: "Übersicht", current: true },
              { href: "#data", label: "Details" },
            ]}
          />
          <MetadataList
            items={[
              { term: "Quelle", description: "FRONT-00 Fixture" },
              { term: "Stand", description: "Candidate 0.1.1" },
            ]}
          />
          <StructuredList>
            <li>Strukturierter Eintrag</li>
            <li>Weiterer Eintrag</li>
          </StructuredList>
          <AccessibleTableContainer label="Komponentenstatus">
            <table>
              <caption>Native Tabelle im zugänglichen Scroll-Container</caption>
              <thead>
                <tr>
                  <th scope="col">Muster</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row">Tabelle</th>
                  <td>Candidate</td>
                </tr>
              </tbody>
            </table>
          </AccessibleTableContainer>
          <Pagination current={1} total={2} />
          <ProvenancePanel
            correctionHref="#"
            source="EPD_Front.zip"
            version="0.1.1-candidate"
          />
        </Card>
      </section>
      <section className="section-block">
        <h2>State catalogue</h2>
        <div className="grid">
          {PRESENTATION_STATES.map((state) => (
            <StatePanel
              key={state}
              state={state}
              title={state.replaceAll("_", " ")}
            >
              <p>Sichtbare, nicht-produktive Fixture für diesen Zustand.</p>
            </StatePanel>
          ))}
        </div>
      </section>
    </WorkspaceShell>
  );
}
