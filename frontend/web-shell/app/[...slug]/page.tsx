import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PublicPageView } from "../../components/public-site";
import { allPublicPages, publicPageByPath } from "../../public/content";
import {
  publicFixtureByPath,
  publicFixtureDetails,
} from "../../public/front02-fixtures";
import { PublicFixtureDetailView } from "../../components/public-fixture-detail";

type Props = { params: Promise<{ slug: string[] }> };

export function generateStaticParams() {
  return allPublicPages
    .filter((page) => page.path !== "/")
    .map((page) => ({ slug: page.path.slice(1).split("/") }))
    .concat(
      publicFixtureDetails.map((detail) => ({
        slug: detail.path.slice(1).split("/"),
      })),
    );
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const page = publicPageByPath.get(`/${slug.join("/")}`);
  return {
    title: page ? `${page.title} · EPD²` : "Seite nicht gefunden · EPD²",
    description: page?.lead,
  };
}

export default async function PublicRoute({ params }: Props) {
  const { slug } = await params;
  const route = `/${slug.join("/")}`;
  const page = publicPageByPath.get(route);
  const detail = publicFixtureByPath.get(route);
  const detailFamily =
    [
      "aktuelles",
      "presse",
      "termine",
      "regionen",
      "personen",
      "wahlen",
    ].includes(slug[0] ?? "") && slug.length === 2;
  if (detailFamily && !detail) notFound();
  if (detail) return <PublicFixtureDetailView detail={detail} />;
  if (!page) notFound();
  return <PublicPageView page={page} />;
}
