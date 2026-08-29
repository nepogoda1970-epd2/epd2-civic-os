import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      ["/home", "/"],
      ["/principles", "/grundsaetze"],
      ["/participate", "/mitmachen"],
      ["/structure", "/struktur"],
      ["/news", "/aktuelles"],
      ["/elections", "/wahlen"],
      ["/aktuelle-wahlen", "/wahlen"],
      ["/donate", "/spenden"],
      ["/technology", "/technologie"],
      ["/roadmap", "/status"],
      ["/faq", "/hilfe"],
      ["/kandidieren", "/kandidatur"],
      ["/mitglied-werden", "/mitgliedschaft"],
    ].map(([source, destination]) => ({
      source,
      destination,
      permanent: true,
    }));
  },
};

export default nextConfig;
