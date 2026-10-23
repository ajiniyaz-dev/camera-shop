import { AccentBar, focusLight } from "@/components/public/brand-mark";
import type { Company } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function contactFields(company: Company, locale: PublicLocale) {
  const text = messages[locale];
  return [
    company.phone ? { label: text.phone, value: company.phone, href: `tel:${company.phone}` } : null,
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
    <section className="overflow-hidden rounded-xl border border-line bg-white shadow-card" aria-labelledby="contact-heading">
      <AccentBar />
      <div className="p-6 sm:p-8">
        <h2 id="contact-heading" className="text-2xl font-semibold tracking-tight text-ink">
          {text.contact}
        </h2>
        {fields.length ? (
          <dl className="mt-6 grid gap-5 border-t border-line pt-6 sm:grid-cols-2">
            {fields.map((field) => (
              <div key={field.label}>
                <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-brand">{field.label}</dt>
                <dd className="mt-1 text-ink">
                  {field.href ? (
                    <a className={`underline-offset-4 hover:underline ${focusLight}`} href={field.href}>
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
          <ul className="mt-6 flex flex-wrap gap-4">
            {company.social_links.map((link) => (
              <li key={link.url}>
                <a className={`text-brand underline underline-offset-4 ${focusLight}`} href={link.url}>
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
}
