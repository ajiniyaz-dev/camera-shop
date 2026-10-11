import { ContactDetails } from "@/components/public/contact-details";
import { publicGet, requireLocale, type Company } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";

export default async function ContactPage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = await requireLocale(params);
  const text = messages[locale];
  const company = await publicGet<Company>(`/api/public/company?locale=${locale}`);
  const details = <ContactDetails company={company} locale={locale} />;
  return (
    <main className="space-y-6">
      <h1 className="text-3xl font-semibold">{text.contact}</h1>
      <p className="text-lg font-medium">{company.name}</p>
      {details}
    </main>
  );
}
