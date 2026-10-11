import type { Company } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function SiteFooter({ locale, company }: { locale: PublicLocale; company: Company }) {
  const text = messages[locale];
  const contacts = [
    company.phone ? { label: text.phone, value: company.phone } : null,
    company.email ? { label: text.email, value: company.email } : null,
    company.address ? { label: text.address, value: company.address } : null,
    company.opening_hours ? { label: text.hours, value: company.opening_hours } : null,
  ].filter((item): item is { label: string; value: string } => item !== null);
  return (
    <footer className="mt-16 border-t border-slate-200 bg-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-slate-800">
        <p className="font-semibold text-slate-950">{company.name}</p>
        {contacts.length ? (
          <ul className="space-y-1">
            {contacts.map((item) => (
              <li key={item.label}>
                <span className="text-slate-600">{item.label}: </span>
                {item.label === text.email ? (
                  <a className="underline underline-offset-4" href={`mailto:${item.value}`}>
                    {item.value}
                  </a>
                ) : (
                  item.value
                )}
              </li>
            ))}
          </ul>
        ) : null}
        {company.social_links?.length ? (
          <ul className="flex flex-wrap gap-4">
            {company.social_links.map((link) => (
              <li key={link.url}>
                <a className="underline underline-offset-4" href={link.url}>
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </footer>
  );
}
