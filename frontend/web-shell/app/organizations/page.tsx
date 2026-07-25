import Link from "next/link";

import { Bilingual, formatDate } from "./Bilingual";
import { SAMPLE_ORGANIZATIONS } from "./data";
import { LABELS, STATUS_LABELS } from "./labels";

export const metadata = {
  title: "Organisationen (Organizations) — EPD² Civic OS",
};

/**
 * Organization browser — read-only, static sample data only (see data.ts).
 * No bulk cross-regional directory and no public member directory are
 * exposed here, per this pack's explicit OpenAPI scope decision
 * (contracts/openapi/pack-08.yaml).
 */
export default function OrganizationsPage() {
  return (
    <main lang="de">
      <h1>
        <Bilingual pair={LABELS.organizationsHeading} />
      </h1>
      <p>
        <Bilingual pair={LABELS.organizationsIntro} />
      </p>

      <table>
        <caption className="visually-hidden">
          {LABELS.organizationsHeading.de} / {LABELS.organizationsHeading.en}
        </caption>
        <thead>
          <tr>
            <th scope="col">
              <Bilingual pair={LABELS.name} />
            </th>
            <th scope="col">
              <Bilingual pair={LABELS.organizationType} />
            </th>
            <th scope="col">
              <Bilingual pair={LABELS.status} />
            </th>
            <th scope="col">
              <Bilingual pair={LABELS.effectiveFrom} />
            </th>
            <th scope="col">
              <Bilingual pair={LABELS.details} />
            </th>
          </tr>
        </thead>
        <tbody>
          {SAMPLE_ORGANIZATIONS.map((organization) => (
            <tr key={organization.organization_id}>
              <td>{organization.name}</td>
              <td>{organization.organization_type}</td>
              <td>
                <Bilingual
                  pair={
                    STATUS_LABELS[organization.status] ?? {
                      de: organization.status,
                      en: organization.status,
                    }
                  }
                />
              </td>
              <td>{formatDate(organization.effective_from)}</td>
              <td>
                <Link href={`/organizations/${organization.organization_id}`}>
                  <Bilingual pair={LABELS.details} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p>
        <Link href="/organizations/dev-authorization-console">
          {LABELS.devConsoleHeading.de}{" "}
          <span lang="en">({LABELS.devConsoleHeading.en})</span>
        </Link>
      </p>
    </main>
  );
}
