import type { Metadata } from "next";

import "./globals.css";
import "./front02.css";

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
      <body>{children}</body>
    </html>
  );
}
