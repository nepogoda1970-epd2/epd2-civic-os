import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "EPD² Civic OS",
  description: "EPD² Civic OS — FRONT-00 frontend foundation candidate",
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
