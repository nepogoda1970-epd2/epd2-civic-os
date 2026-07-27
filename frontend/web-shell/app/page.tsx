import { PublicPageView } from "../components/public-site";
import { publicPageByPath } from "../public/content";

export default function Home() {
  return <PublicPageView page={publicPageByPath.get("/")!} />;
}
