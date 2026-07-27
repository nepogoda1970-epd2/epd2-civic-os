import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { PublicPageView } from "../../components/public-site";
import { publicPageByPath, publicPages } from "../../public/content";

type Props = { params: Promise<{ slug: string[] }> };

export function generateStaticParams() {
  return publicPages
    .filter((page) => page.path !== "/")
    .map((page) => ({ slug: page.path.slice(1).split("/") }));
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
  const page = publicPageByPath.get(`/${slug.join("/")}`);
  if (!page) notFound();
  return <PublicPageView page={page} />;
}
