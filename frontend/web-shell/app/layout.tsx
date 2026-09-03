import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "EPD² — politische Beteiligung nachvollziehbar aufgebaut",
  description:
    "Öffentliche Website des EPD² Projekts mit sichtbaren Reifegraden und Aktivierungsgrenzen.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <head>
        <script
          // The URL is the sole locale state.  This runs before hydration so a
          // directly opened English URL never remains labelled as German.
          dangerouslySetInnerHTML={{
            __html:
              "document.documentElement.lang=new URLSearchParams(location.search).get('lang')==='en'?'en':'de';",
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
