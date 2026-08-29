import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PublicPageView } from "../../components/public-site";
import { publicPages, publicPageByPath } from "../../public/content";
import { front02PageByPath, front02PublicPages } from "../../public/front02-content";

type Props = { params: Promise<{ slug: string[] }> };

export function generateStaticParams() {
  return [...publicPages, ...front02PublicPages]
    .filter((page) => page.path !== "/")
    .map((page) => ({ slug: page.path.slice(1).split("/") }));
}

function pageFor(path: string) {
  return front02PageByPath.get(path) ?? publicPageByPath.get(path);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const page = pageFor(`/${slug.join("/")}`);
  return {
    title: page ? `${page.title} · EPD²` : "Seite nicht gefunden · EPD²",
    description: page?.lead,
  };
}

export default async function PublicRoute({ params }: Props) {
  const { slug } = await params;
  const path = `/${slug.join("/")}`;
  const page = pageFor(path);
  const detailFamily =
    ["aktuelles", "presse", "termine", "regionen", "personen", "wahlen"].includes(
      slug[0] ?? "",
    ) && slug.length === 2;
  if (detailFamily && !page) {
    return (
      <PublicPageView
        page={{
          id: "FRONT02-UNAVAILABLE-DETAIL",
          path,
          title: "Öffentliche Rendition nicht verfügbar",
          eyebrow: "Kein Datensatz wird vorausgesetzt",
          lead: "Diese Detailansicht zeigt erst dann Inhalt, wenn eine zuständige Quelle eine freigegebene öffentliche Rendition bereitstellt.",
          status: "planned",
          pack: "PACK-28 / WS-10",
          prerequisites: "Freigegebene, versionierte Publikationsprojektion",
          kind: "standard",
          sections: [{ title: "Was jetzt möglich ist", text: "Zurück zur Übersicht wechseln oder öffentliche Hilfe nutzen. Es werden weder interne Daten noch fiktive Inhalte angezeigt." }],
        }}
      />
    );
  }
  if (!page) notFound();
  return <PublicPageView page={page} />;
}
