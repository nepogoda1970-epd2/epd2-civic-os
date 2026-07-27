import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "EPD² Civic OS",
  description: "EPD² Civic OS — infrastructure skeleton",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
