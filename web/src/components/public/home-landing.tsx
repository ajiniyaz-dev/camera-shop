import Link from "next/link";
import {
  Building2,
  Cable,
  Camera,
  HardDrive,
  Home,
  MonitorSmartphone,
  Moon,
  Network,
  ShieldCheck,
  Store,
  Video,
  Warehouse,
  type LucideIcon,
} from "lucide-react";

import { focusLight } from "@/components/public/brand-mark";
import { ContactDetails, contactFields } from "@/components/public/contact-details";
import {
  LANDING_SOLUTIONS,
  LANDING_SYSTEM_PARTS,
  LANDING_TECHNOLOGIES,
  availableLandingCategories,
  categoryHref,
  firstCategoryHref,
  techHref,
  type LandingCategoryRef,
  type LandingSolutionId,
  type LandingSystemId,
  type LandingTechId,
} from "@/lib/home-landing";
import type { CategoryNode, Company } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";
import { selectionNavHref } from "@/lib/selection";

const TECH_ICONS: Record<LandingTechId, LucideIcon> = {
  colorvu: Video,
  acusense: ShieldCheck,
  darkfighter: Moon,
  hikconnect: MonitorSmartphone,
};

const SOLUTION_ICONS: Record<LandingSolutionId, LucideIcon> = {
  home: Home,
  retail: Store,
  office: Building2,
  warehouse: Warehouse,
};

const SYSTEM_ICONS: Record<LandingSystemId, LucideIcon> = {
  cameras: Camera,
  recorder: Video,
  storage: HardDrive,
  network: Network,
};

function techCopy(id: LandingTechId, text: (typeof messages)[PublicLocale]) {
  switch (id) {
    case "colorvu":
      return { title: text.landingTechColorVuTitle, body: text.landingTechColorVuBody };
    case "acusense":
      return { title: text.landingTechAcuSenseTitle, body: text.landingTechAcuSenseBody };
    case "darkfighter":
      return { title: text.landingTechDarkFighterTitle, body: text.landingTechDarkFighterBody };
    case "hikconnect":
      return { title: text.landingTechHikConnectTitle, body: text.landingTechHikConnectBody };
  }
}

function solutionCopy(id: LandingSolutionId, text: (typeof messages)[PublicLocale]) {
  switch (id) {
    case "home":
      return { title: text.landingSolutionHomeTitle, body: text.landingSolutionHomeBody };
    case "retail":
      return { title: text.landingSolutionRetailTitle, body: text.landingSolutionRetailBody };
    case "office":
      return { title: text.landingSolutionOfficeTitle, body: text.landingSolutionOfficeBody };
    case "warehouse":
      return { title: text.landingSolutionWarehouseTitle, body: text.landingSolutionWarehouseBody };
  }
}

function systemCopy(id: LandingSystemId, text: (typeof messages)[PublicLocale]) {
  switch (id) {
    case "cameras":
      return { title: text.landingSystemCamerasTitle, body: text.landingSystemCamerasBody };
    case "recorder":
      return { title: text.landingSystemRecorderTitle, body: text.landingSystemRecorderBody };
    case "storage":
      return { title: text.landingSystemStorageTitle, body: text.landingSystemStorageBody };
    case "network":
      return { title: text.landingSystemNetworkTitle, body: text.landingSystemNetworkBody };
  }
}

export function HomeLandingSections({
  locale,
  categories,
  company,
}: {
  locale: PublicLocale;
  categories: CategoryNode[];
  company: Company;
}) {
  const text = messages[locale];
  const flatCategories = flattenCategories(categories);
  const available = availableLandingCategories(flatCategories);
  const hasContact = contactFields(company, locale).length > 0 || (company.social_links?.length ?? 0) > 0;
  const contactPath = `/${locale}/contact`;
  const cartPath = selectionNavHref(locale);
  const steps = [
    { title: text.landingStep1Title, body: text.landingStep1Body },
    { title: text.landingStep2Title, body: text.landingStep2Body },
    { title: text.landingStep3Title, body: text.landingStep3Body },
    { title: text.landingStep4Title, body: text.landingStep4Body },
  ] as const;

  return (
    <>
      <section className="space-y-5" aria-labelledby="landing-tech-heading">
        <LandingHeading id="landing-tech-heading" title={text.landingTechTitle} intro={text.landingTechIntro} />
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {LANDING_TECHNOLOGIES.map((tech) => {
            const copy = techCopy(tech.id, text);
            const Icon = TECH_ICONS[tech.id];
            const link = techHref(tech, locale, available);
            const softBrowse = tech.id === "darkfighter" ? categoryHref(locale, "ip-kamery", available) : null;
            return (
              <li key={tech.id} className="min-w-0">
                <article className="flex h-full flex-col surface-card p-5">
                  <span className="grid h-11 w-11 place-items-center rounded-lg bg-mist text-brand" aria-hidden="true">
                    <Icon className="h-5 w-5" strokeWidth={1.75} />
                  </span>
                  <h3 className="mt-4 text-lg font-semibold tracking-tight text-ink">{copy.title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-6 text-mute">{copy.body}</p>
                  {link ? (
                    <Link href={link.href} className={`mt-4 inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
                      {link.kind === "contact" ? text.landingConsultCta : text.landingBrowseSection}
                    </Link>
                  ) : softBrowse ? (
                    <Link href={softBrowse} className={`mt-4 inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
                      {text.landingBrowseSection}
                    </Link>
                  ) : null}
                </article>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="overflow-hidden rounded-2xl bg-navy px-5 py-8 text-white shadow-card sm:px-8 sm:py-10" aria-labelledby="landing-solutions-heading">
        <div className="max-w-2xl">
          <div aria-hidden="true" className="mb-3 h-1 w-8 rounded-full bg-teal" />
          <h2 id="landing-solutions-heading" className="text-2xl font-semibold tracking-tight">
            {text.landingSolutionsTitle}
          </h2>
          <p className="mt-2 text-sm leading-6 text-white/75">{text.landingSolutionsIntro}</p>
        </div>
        <ul className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {LANDING_SOLUTIONS.map((solution) => {
            const copy = solutionCopy(solution.id, text);
            const Icon = SOLUTION_ICONS[solution.id];
            const href = firstCategoryHref(locale, solution.categorySlugs, available);
            return (
              <li key={solution.id} className="min-w-0">
                <article className="flex h-full flex-col rounded-xl border border-white/15 bg-white/5 p-5 backdrop-blur-sm">
                  <span className="grid h-11 w-11 place-items-center rounded-lg bg-white/10 text-sky" aria-hidden="true">
                    <Icon className="h-5 w-5" strokeWidth={1.75} />
                  </span>
                  <h3 className="mt-4 text-lg font-semibold tracking-tight text-white">{copy.title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-6 text-white/70">{copy.body}</p>
                  {href ? (
                    <Link href={href} className="mt-4 inline-flex min-h-11 items-center text-sm font-medium text-sky underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
                      {text.landingBrowseSection}
                    </Link>
                  ) : null}
                </article>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="space-y-5" aria-labelledby="landing-system-heading">
        <LandingHeading id="landing-system-heading" title={text.landingSystemTitle} intro={text.landingSystemIntro} />
        <p className="rounded-xl border border-line bg-mist/70 px-4 py-3 text-sm leading-6 text-mute">{text.landingSystemNote}</p>
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {LANDING_SYSTEM_PARTS.map((part) => {
            const copy = systemCopy(part.id, text);
            const Icon = SYSTEM_ICONS[part.id];
            const links = part.categorySlugs
              .map((slug) => {
                const category = available.get(slug);
                const href = categoryHref(locale, slug, available);
                return href && category ? { href, label: category.name } : null;
              })
              .filter((item): item is { href: string; label: string } => item !== null);
            return (
              <li key={part.id} className="min-w-0">
                <article className="flex h-full flex-col surface-card p-5 sm:flex-row sm:gap-4">
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-mist text-brand" aria-hidden="true">
                    {part.id === "network" ? <Cable className="h-5 w-5" strokeWidth={1.75} /> : <Icon className="h-5 w-5" strokeWidth={1.75} />}
                  </span>
                  <div className="mt-4 min-w-0 flex-1 sm:mt-0">
                    <h3 className="text-lg font-semibold tracking-tight text-ink">{copy.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-mute">{copy.body}</p>
                    {links.length ? (
                      <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
                        {links.map((link) => (
                          <li key={link.href}>
                            <Link href={link.href} className={`inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
                              {link.label}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                </article>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="space-y-5" aria-labelledby="landing-steps-heading">
        <LandingHeading id="landing-steps-heading" title={text.landingStepsTitle} intro={text.landingStepsIntro} />
        <ol className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, index) => (
            <li key={step.title} className="min-w-0">
              <article className="relative flex h-full flex-col overflow-hidden rounded-xl border border-line bg-white p-5 shadow-card">
                <span className="text-4xl font-semibold leading-none text-sky/40" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-3 text-base font-semibold tracking-tight text-ink">{step.title}</h3>
                <p className="mt-2 flex-1 text-sm leading-6 text-mute">{step.body}</p>
              </article>
            </li>
          ))}
        </ol>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link href={cartPath} className="btn-secondary">
            {text.landingOpenCart}
          </Link>
          <Link href={contactPath} className="btn-primary">
            {text.landingConsultCta}
          </Link>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl bg-gradient-to-br from-navy via-navy to-[#152a52] text-white shadow-card" aria-labelledby="landing-consult-heading">
        <div className="px-5 py-8 sm:px-8 sm:py-10 lg:flex lg:items-end lg:justify-between lg:gap-10">
          <div className="max-w-2xl">
            <div aria-hidden="true" className="mb-3 h-1 w-8 rounded-full bg-teal" />
            <h2 id="landing-consult-heading" className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {text.landingConsultTitle}
            </h2>
            <p className="mt-3 text-sm leading-6 text-white/75 sm:text-base">{text.landingConsultIntro}</p>
          </div>
          <div className="mt-6 flex shrink-0 flex-col gap-3 sm:flex-row lg:mt-0">
            <Link href={contactPath} className="btn-on-dark">
              {text.landingConsultCta}
            </Link>
            <Link href={`/${locale}/catalog`} className="btn-ghost">
              {text.browseCatalog}
            </Link>
          </div>
        </div>
      </section>

      {hasContact ? <ContactDetails company={company} locale={locale} /> : null}
    </>
  );
}

function flattenCategories(nodes: CategoryNode[], parentSlug: string | null = null): LandingCategoryRef[] {
  const out: LandingCategoryRef[] = [];
  for (const node of nodes) {
    out.push({ slug: node.slug, name: node.name, parentSlug });
    if (node.children?.length) out.push(...flattenCategories(node.children, node.slug));
  }
  return out;
}

function LandingHeading({ id, title, intro }: { id: string; title: string; intro: string }) {
  return (
    <div className="border-b border-line pb-4">
      <div aria-hidden="true" className="accent-rail mb-2" />
      <h2 id={id} className="text-2xl font-semibold tracking-tight text-ink">
        {title}
      </h2>
      <p className="mt-1 max-w-3xl text-sm leading-6 text-mute">{intro}</p>
    </div>
  );
}
