import type { Metadata } from "next";
import { headers } from "next/headers";
import type { ReactNode } from "react";

import { publicOrigin } from "@/lib/seo";

import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const origin = publicOrigin();
  return {
    metadataBase: origin ? new URL(origin) : undefined,
    title: "HikVision catalog",
    description: "Informational product catalog",
  };
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const requested = (await headers()).get("x-catalog-locale");
  const lang = requested === "ru" || requested === "uz" || requested === "en" ? requested : "en";
  return (
    <html lang={lang}>
      <body className="bg-white text-neutral-950 antialiased">{children}</body>
    </html>
  );
}
