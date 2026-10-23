import Link from "next/link";
import { Building2, Home, Moon, MonitorSmartphone, ShieldCheck, Store, Video, Warehouse, type LucideIcon } from "lucide-react";

import { focusLight } from "@/components/public/brand-mark";
import {
  LANDING_SOLUTIONS,
  LANDING_TECHNOLOGIES,
  availableLandingCategories,
  categoryHref,
  firstCategoryHref,
  techHref,
  type LandingCategoryRef,
  type LandingSolutionId,
  type LandingTechId,
} from "@/lib/home-landing";
import type { CategoryNode } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

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

function techCopy(id: LandingTechId, text: (typeof messages)[PublicLocale]) {
  switch (id) {
    case "colorvu": return { title: text.landingTechColorVuTitle, body: text.landingTechColorVuBody };
    case "acusense": return { title: text.landingTechAcuSenseTitle, body: text.landingTechAcuSenseBody };
    case "darkfighter": return { title: text.landingTechDarkFighterTitle, body: text.landingTechDarkFighterBody };
    case "hikconnect": return { title: text.landingTechHikConnectTitle, body: text.landingTechHikConnectBody };
  }
}

function solutionCopy(id: LandingSolutionId, text: (typeof messages)[PublicLocale]) {
  switch (id) {
    case "home": return { title: text.landingSolutionHomeTitle, body: text.landingSolutionHomeBody };
    case "retail": return { title: text.landingSolutionRetailTitle, body: text.landingSolutionRetailBody };
    case "office": return { title: text.landingSolutionOfficeTitle, body: text.landingSolutionOfficeBody };
    case "warehouse": return { title: text.landingSolutionWarehouseTitle, body: text.landingSolutionWarehouseBody };
  }
}

export function HomeDiscoverySections({ locale, categories }: { locale: PublicLocale; categories: CategoryNode[] }) {
  const text = messages[locale];
  const available = availableLandingCategories(flattenCategories(categories));

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
                  <span className="grid h-11 w-11 place-items-center rounded-lg bg-mist text-brand" aria-hidden="true"><Icon className="h-5 w-5" strokeWidth={1.75} /></span>
                  <h3 className="mt-4 text-lg font-semibold tracking-tight text-[#1D4ED8]">{copy.title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-6 text-[#334155]">{copy.body}</p>
                  {link ? <Link href={link.href} className={`mt-4 inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>{link.kind === "contact" ? text.landingConsultCta : text.landingBrowseSection}</Link> : softBrowse ? <Link href={softBrowse} className={`mt-4 inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>{text.landingBrowseSection}</Link> : null}
                </article>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="overflow-hidden rounded-2xl bg-[#F5F7FA] px-5 py-8 sm:px-8 sm:py-10" aria-labelledby="landing-solutions-heading">
        <div className="max-w-2xl">
          <div aria-hidden="true" className="mb-3 h-1 w-8 rounded-full bg-[#2563EB]" />
          <h2 id="landing-solutions-heading" className="text-2xl font-semibold tracking-tight text-[#1D4ED8]">{text.landingSolutionsTitle}</h2>
          <p className="mt-2 text-sm leading-6 text-[#334155]">{text.landingSolutionsIntro}</p>
        </div>
        <ul className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {LANDING_SOLUTIONS.map((solution) => {
            const copy = solutionCopy(solution.id, text);
            const Icon = SOLUTION_ICONS[solution.id];
            const href = firstCategoryHref(locale, solution.categorySlugs, available);
            return (
              <li key={solution.id} className="min-w-0">
                <article className="flex h-full flex-col rounded-xl bg-white p-5 shadow-sm">
                  <span className="grid h-11 w-11 place-items-center rounded-lg bg-[#F5F7FA] text-[#2563EB]" aria-hidden="true"><Icon className="h-5 w-5" strokeWidth={1.75} /></span>
                  <h3 className="mt-4 text-lg font-semibold tracking-tight text-[#1D4ED8]">{copy.title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-6 text-[#334155]">{copy.body}</p>
                  {href ? <Link href={href} className="mt-4 inline-flex min-h-11 items-center text-sm font-medium text-[#2563EB] underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#2563EB]">{text.landingBrowseSection}</Link> : null}
                </article>
              </li>
            );
          })}
        </ul>
      </section>
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
  return <div className="border-b border-[#E5E7EB] pb-4"><div aria-hidden="true" className="mb-2 h-1 w-8 rounded-full bg-[#2563EB]" /><h2 id={id} className="text-2xl font-semibold tracking-tight text-[#1D4ED8]">{title}</h2><p className="mt-1 max-w-3xl text-sm leading-6 text-[#334155]">{intro}</p></div>;
}
