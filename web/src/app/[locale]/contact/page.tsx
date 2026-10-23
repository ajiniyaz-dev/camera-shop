import type { Metadata } from "next";

import { ContactDetails } from "@/components/public/contact-details";
import { PageHeading } from "@/components/public/page-heading";
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
      <PageHeading title={text.contact} description={company.name} />
      <section className="w-full rounded-xl bg-[#F5F7FA] px-5 py-5 sm:px-7 sm:py-6" aria-labelledby="contact-info-heading">
        <h2 id="contact-info-heading" className="text-lg font-semibold tracking-tight text-[#1D4ED8] sm:text-xl">{text.contactInfoTitle}</h2>
        <p className="mt-2 text-base leading-7 text-[#000000]">{text.contactInfoBody}</p>
      </section>
      {details}
    </main>
  );
}
