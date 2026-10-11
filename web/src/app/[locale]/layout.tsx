import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SiteFooter } from "@/components/public/site-footer";
import { SiteHeader } from "@/components/public/site-header";
import { publicGet, requireLocale, type Company } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const locale = await requireLocale(params);
  return { title: `HikVision — ${messages[locale].catalog}` };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const locale = await requireLocale(params);
  const company = await publicGet<Company>(`/api/public/company?locale=${locale}`);
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader locale={locale} company={company} />
      <div className="mx-auto w-full max-w-6xl flex-1 px-4 py-8" id="content">
        {children}
      </div>
      <SiteFooter locale={locale} company={company} />
    </div>
  );
}
