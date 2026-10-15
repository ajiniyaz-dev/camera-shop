import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SiteFooter } from "@/components/public/site-footer";
import { SiteHeader } from "@/components/public/site-header";
import { loadPublic, requireLocale, type Company } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
import { SITE_NAME } from "@/lib/seo";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const locale = await requireLocale(params);
  return { title: { absolute: `${SITE_NAME} | ${messages[locale].catalog}` } };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const locale = await requireLocale(params);
  const company = await loadPublic<Company>(`/api/public/company?locale=${locale}`);
  return (
    <div className="flex min-h-screen flex-col bg-mist text-navy">
      <SiteHeader locale={locale} company={company} />
      <div className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:py-12" id="content">
        {children}
      </div>
      <SiteFooter locale={locale} company={company} />
    </div>
  );
}
