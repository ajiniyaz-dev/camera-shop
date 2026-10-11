import type { Metadata } from "next";

import { ContactDetails } from "@/components/public/contact-details";
import { JsonLd } from "@/components/public/json-ld";
import { loadPublic, requireLocale, type Company } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
import { organizationJson, pageMetadata, SITE_NAME } from "@/lib/seo";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const locale = await requireLocale(params);
  const company = await loadPublic<Company>(`/api/public/company?locale=${locale}`);
  const text = messages[locale];
  return pageMetadata({
    locale,
    title: `${text.contact} | ${SITE_NAME}`,
    description: `${company.name}. ${text.contact}`,
    path: `/${locale}/contact`,
    index: true,
  });
}

export default async function ContactPage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = await requireLocale(params);
  const text = messages[locale];
  const company = await loadPublic<Company>(`/api/public/company?locale=${locale}`);
  const details = <ContactDetails company={company} locale={locale} />;
  return (
    <main className="space-y-6">
      <JsonLd data={organizationJson(company)} />
      <h1 className="text-3xl font-semibold">{text.contact}</h1>
      <p className="text-lg font-medium">{company.name}</p>
      {details}
    </main>
  );
}
