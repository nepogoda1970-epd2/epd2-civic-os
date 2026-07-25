import Link from "next/link";
import { notFound } from "next/navigation";

import { Bilingual, formatDate } from "../Bilingual";
import { AsOfSelector } from "../AsOfSelector";
import {
  authoritiesForScope,
  findOrganization,
  RELATION_CATEGORY_BY_TYPE,
  relationsForOrganization,
  SAMPLE_ORGANIZATIONS,
} from "../data";
import {
  LABELS,
  RELATION_CATEGORY_LABELS,
  RELATION_TYPE_LABELS,
  ROLE_LABELS,
  STATUS_LABELS,
} from "../labels";

export function generateStaticParams() {
  return SAMPLE_ORGANIZATIONS.map((organization) => ({
    id: organization.organization_id,
  }));
}

export default async function OrganizationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const organization = findOrganization(id);
  if (!organization) {
    notFound();
    return null;
  }

  const relations = relationsForOrganization(organization.organization_id);
  const authorities = authoritiesForScope(organization.organization_id);
  const parent = organization.parent_reference
    ? findOrganization(organization.parent_reference)
    : undefined;
  const successor = organization.successor_reference
    ? findOrganization(organization.successor_reference)
    : undefined;

  return (
    <main lang="de">
      <p>
        <Link href="/organizations">
          &larr; <Bilingual pair={LABELS.backToList} />
        </Link>
      </p>

      <h1>{organization.name}</h1>

      <dl>
        <dt>
          <Bilingual pair={LABELS.legalOperator} />
        </dt>
        <dd>{organization.legal_operator}</dd>

        <dt>
          <Bilingual pair={LABELS.organizationType} />
        </dt>
        <dd>{organization.organization_type}</dd>

        <dt>
          <Bilingual pair={LABELS.status} />
        </dt>
        <dd>
          <Bilingual
            pair={
              STATUS_LABELS[organization.status] ?? {
                de: organization.status,
                en: organization.status,
              }
            }
          />
        </dd>

        <dt>
          <Bilingual pair={LABELS.effectiveFrom} />
        </dt>
        <dd>{formatDate(organization.effective_from)}</dd>

        <dt>
          <Bilingual pair={LABELS.effectiveUntil} />
        </dt>
        <dd>{formatDate(organization.effective_until)}</dd>

        {organization.dissolved_at && (
          <>
            <dt>
              <Bilingual pair={LABELS.dissolvedAt} />
            </dt>
            <dd>{formatDate(organization.dissolved_at)}</dd>
          </>
        )}

        {parent && (
          <>
            <dt>
              <Bilingual pair={LABELS.parentOrganization} />
            </dt>
            <dd>
              <Link href={`/organizations/${parent.organization_id}`}>
                {parent.name}
              </Link>
            </dd>
          </>
        )}

        {successor && (
          <>
            <dt>
              <Bilingual pair={LABELS.successor} />
            </dt>
            <dd>
              <Link href={`/organizations/${successor.organization_id}`}>
                {successor.name}
              </Link>
            </dd>
          </>
        )}
      </dl>

      <section aria-labelledby="as-of-heading">
        <h2 id="as-of-heading">
          <Bilingual pair={LABELS.currentStatusAsOf} />
        </h2>
        <AsOfSelector
          history={organization.status_history}
          statusLabels={STATUS_LABELS}
        />
      </section>

      <section aria-labelledby="relations-heading">
        <h2 id="relations-heading">
          <Bilingual pair={LABELS.relationsHeading} />
        </h2>
        <p>
          <Bilingual pair={LABELS.relationsIntro} />
        </p>
        {relations.length === 0 ? (
          <p>
            <Bilingual pair={LABELS.noRelations} />
          </p>
        ) : (
          <table>
            <caption className="visually-hidden">
              {LABELS.relationsHeading.de}
            </caption>
            <thead>
              <tr>
                <th scope="col">
                  <Bilingual pair={LABELS.relationType} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.relationCategory} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.source} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.target} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.validFrom} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.validUntil} />
                </th>
              </tr>
            </thead>
            <tbody>
              {relations.map((relation) => {
                const source = findOrganization(
                  relation.source_organization_id,
                );
                const target = findOrganization(
                  relation.target_organization_id,
                );
                return (
                  <tr key={relation.relation_id}>
                    <td>
                      <Bilingual
                        pair={RELATION_TYPE_LABELS[relation.relation_type]}
                      />
                    </td>
                    <td>
                      <Bilingual
                        pair={
                          RELATION_CATEGORY_LABELS[
                            RELATION_CATEGORY_BY_TYPE[relation.relation_type]
                          ]
                        }
                      />
                    </td>
                    <td>
                      {source ? (
                        <Link href={`/organizations/${source.organization_id}`}>
                          {source.name}
                        </Link>
                      ) : (
                        relation.source_organization_id
                      )}
                    </td>
                    <td>
                      {target ? (
                        <Link href={`/organizations/${target.organization_id}`}>
                          {target.name}
                        </Link>
                      ) : (
                        relation.target_organization_id
                      )}
                    </td>
                    <td>{formatDate(relation.valid_from)}</td>
                    <td>{formatDate(relation.valid_until)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>

      <section aria-labelledby="authorities-heading">
        <h2 id="authorities-heading">
          <Bilingual pair={LABELS.authoritiesHeading} />
        </h2>
        <p>
          <Bilingual pair={LABELS.authoritiesIntro} />
        </p>
        {authorities.length === 0 ? (
          <p>
            <Bilingual pair={LABELS.noAuthorities} />
          </p>
        ) : (
          <table>
            <caption className="visually-hidden">
              {LABELS.authoritiesHeading.de}
            </caption>
            <thead>
              <tr>
                <th scope="col">
                  <Bilingual pair={LABELS.roleCode} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.subject} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.proceduralAuthority} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.dataAccess} />
                </th>
                <th scope="col">
                  <Bilingual pair={LABELS.validFrom} />
                </th>
              </tr>
            </thead>
            <tbody>
              {authorities.map((authority) => (
                <tr key={authority.authority_id}>
                  <td>
                    <Bilingual
                      pair={
                        ROLE_LABELS[authority.role_code] ?? {
                          de: authority.role_code,
                          en: authority.role_code,
                        }
                      }
                    />
                  </td>
                  <td>{authority.assigned_subject_reference}</td>
                  <td>
                    <Bilingual
                      pair={
                        authority.grants_procedural_authority
                          ? LABELS.yes
                          : LABELS.no
                      }
                    />
                  </td>
                  <td>
                    <Bilingual
                      pair={
                        authority.grants_data_access ? LABELS.yes : LABELS.no
                      }
                    />
                  </td>
                  <td>{formatDate(authority.valid_from)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
