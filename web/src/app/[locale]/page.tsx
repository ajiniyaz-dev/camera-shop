import type { Metadata } from "next";
import Link from "next/link";

import { CameraGlyph, focusLight } from "@/components/public/brand-mark";
import { ContactDetails, contactFields } from "@/components/public/contact-details";
import { HomeProductCard } from "@/components/public/home-cards";
import { HomeHero } from "@/components/public/home-hero";
import { HomeDiscoverySections } from "@/components/public/home-landing";
import { JsonLd } from "@/components/public/json-ld";
import { FEATURED_CATEGORY_SLUGS, HERO_CATEGORY_SLUG, selectHomepageProducts } from "@/lib/home-featured";
import {
  PublicCatalogError,
  loadPublic,
  requireLocale,
  type CategoryNode,
  type Company,
  type ProductList,
  type PublicCard,
} from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";
import { organizationJson, pageMetadata, SITE_NAME, websiteJson } from "@/lib/seo";

type HomePayload = {
  company: Company;
  categories: CategoryNode[];
  products: PublicCard[];
};

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const locale = await requireLocale(params);
  const company = await loadPublic<Company>(`/api/public/company?locale=${locale}`);
  return pageMetadata({
    locale,
    title: company.name,
    description: `${company.name}. ${messages[locale].catalog}`,
    path: `/${locale}`,
    index: true,
  });
}

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = await requireLocale(params);
  const text = messages[locale];
  const home = await loadPublic<HomePayload>(`/api/public/home?locale=${locale}`);
  const [heroGroup, ...groups] = await Promise.all([
    productsInCategory(locale, HERO_CATEGORY_SLUG),
    ...FEATURED_CATEGORY_SLUGS.map((slug) => productsInCategory(locale, slug)),
  ]);
  const { hero, featured } = selectHomepageProducts(heroGroup, groups);
  const shown = (featured.length ? featured : home.products).slice(0, 3);
  const hasContact = contactFields(home.company, locale).length > 0 || (home.company.social_links?.length ?? 0) > 0;
  return (
    <main className="-mx-4 -my-6 space-y-12 bg-white px-4 py-6 sm:-my-8 sm:space-y-16 sm:py-8">
      <HomeHero companyName={home.company.name} locale={locale} product={hero ?? shown.find((item) => item.image) ?? null} />

      <section className="space-y-4 rounded-2xl bg-[#F5F7FA] p-4 sm:p-6" aria-labelledby="products-heading">
        <SectionHeading
          id="products-heading"
          title={text.featuredProductsTitle}
          href={`/${locale}/catalog`}
          action={text.catalog}
          prominent
        />
        {shown.length ? (
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 lg:gap-5">
            {shown.map((product) => (
              <li key={product.slug} className="min-w-0">
                <HomeProductCard product={product} locale={locale} />
              </li>
            ))}
          </ul>
        ) : (
          <ProductEmpty title={text.homeEmptyProductsTitle} body={text.homeEmptyProducts} href={`/${locale}/catalog`} action={text.browseCatalog} />
        )}
      </section>

      <HomeDiscoverySections locale={locale} categories={home.categories} />

      {hasContact ? (
        <div className="space-y-3">
          <ContactDetails company={home.company} locale={locale} />
          <div className="flex justify-end">
            <Link href={`/${locale}/contact`} className="btn-secondary">
              {text.contact}
            </Link>
          </div>
        </div>
      ) : null}

      <section className="grid grid-cols-1 gap-x-14 gap-y-6 rounded-2xl bg-[#F5F7FA] p-6 sm:p-10 md:grid-cols-2" aria-labelledby="home-seo-heading">
        <div className="md:col-span-2">
          <div aria-hidden="true" className="mb-2 h-1 w-8 rounded-full bg-[#2563EB]" />
          <h2 id="home-seo-heading" className="text-2xl font-semibold tracking-tight text-[#1D4ED8] sm:text-3xl">
            {text.homeSeoHeading}
          </h2>
        </div>
        <p className="text-base leading-7 text-[#000000]">{text.homeSeoParagraph1}</p>
        <p className="text-base leading-7 text-[#000000]">{text.homeSeoParagraph2}</p>
      </section>

      <JsonLd data={organizationJson(home.company)} />
      <JsonLd data={websiteJson(locale, home.company.name || SITE_NAME)} />
    </main>
  );
}

async function productsInCategory(locale: string, slug: string): Promise<PublicCard[]> {
  try {
    const list = await loadPublic<ProductList>(
      `/api/public/products?locale=${encodeURIComponent(locale)}&category=${encodeURIComponent(slug)}&page=1&page_size=24&sort=model`,
    );
    return list.products;
  } catch (error) {
    if (error instanceof PublicCatalogError) return [];
    throw error;
  }
}

function SectionHeading({
  id,
  title,
  intro,
  href,
  action,
  prominent = false,
}: {
  id: string;
  title: string;
  intro?: string;
  href: string;
  action: string;
  prominent?: boolean;
}) {
  return (
    <div className="flex items-end justify-between gap-4 border-b border-line pb-3">
      <div>
        <div aria-hidden="true" className="mb-2 h-1 w-8 rounded-full bg-[#2563EB]" />
        <h2 id={id} className={`font-semibold tracking-tight text-[#1D4ED8] ${prominent ? "text-2xl sm:text-3xl" : "text-xl sm:text-2xl"}`}>
          {title}
        </h2>
        {intro ? <p className="mt-1 text-sm text-mute">{intro}</p> : null}
      </div>
      <Link href={href} className={`shrink-0 text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
        {action}
      </Link>
    </div>
  );
}

function ProductEmpty({ title, body, href, action }: { title: string; body: string; href: string; action: string }) {
  return (
    <div role="status" className="flex flex-col gap-4 surface-card border-sky/40 p-5 sm:flex-row sm:items-center sm:p-6">
      <span className="grid h-14 w-14 shrink-0 place-items-center rounded-lg bg-navy text-white">
        <CameraGlyph className="h-8 w-8" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-ink">{title}</p>
        <p className="mt-1 max-w-xl text-sm leading-6 text-mute">{body}</p>
      </div>
      <Link href={href} className="btn-primary shrink-0">
        {action}
      </Link>
    </div>
  );
}
