import type { Company } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function contactFields(company: Company, locale: PublicLocale) {
  const text = messages[locale];
  return [
    company.phone ? { label: text.phone, value: company.phone, href: undefined } : null,
    company.email ? { label: text.email, value: company.email, href: `mailto:${company.email}` } : null,
    company.address ? { label: text.address, value: company.address, href: undefined } : null,
    company.opening_hours ? { label: text.hours, value: company.opening_hours, href: undefined } : null,
  ].filter((item): item is { label: string; value: string; href: string | undefined } => item !== null);
}

export function ContactDetails({ company, locale }: { company: Company; locale: PublicLocale }) {
  const text = messages[locale];
  const fields = contactFields(company, locale);
  if (!fields.length && !company.social_links?.length) return null;
  return (
    <section className="space-y-3" aria-labelledby="contact-heading">
      <h2 id="contact-heading" className="text-xl font-semibold">
        {text.contact}
      </h2>
      {fields.length ? (
        <dl className="space-y-2">
          {fields.map((field) => (
            <div key={field.label}>
              <dt className="text-sm text-slate-600">{field.label}</dt>
              <dd>
                {field.href ? (
                  <a className="underline underline-offset-4" href={field.href}>
                    {field.value}
                  </a>
                ) : (
                  field.value
                )}
              </dd>
            </div>
          ))}
        </dl>
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
    </section>
  );
}
