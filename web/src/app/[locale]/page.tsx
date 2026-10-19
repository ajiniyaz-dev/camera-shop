import type { Metadata } from "next";
import Link from "next/link";

import { CameraFigure, CameraGlyph, FolderGlyph, focusLight } from "@/components/public/brand-mark";
import { contactFields } from "@/components/public/contact-details";
import { HomeCategoryCard, HomeHeroProduct, HomeProductCard } from "@/components/public/home-cards";
import { HomeLandingSections } from "@/components/public/home-landing";
import { HomeSearch } from "@/components/public/home-search";
import { JsonLd } from "@/components/public/json-ld";
import {
  FEATURED_CATEGORY_SLUGS,
  HERO_CATEGORY_SLUG,
  SHORTCUT_CATEGORY_SLUGS,
  selectHomepageProducts,
  splitCategories,
} from "@/lib/home-featured";
import {
  PublicCatalogError,
  categoryPath,
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
  const groups = await Promise.all([
    productsInCategory(locale, HERO_CATEGORY_SLUG),
    ...FEATURED_CATEGORY_SLUGS.map((slug) => productsInCategory(locale, slug)),
  ]);
  const { hero, featured } = selectHomepageProducts(groups[0] ?? [], groups.slice(1));
  const shown = featured.length ? featured : home.products;
  const { shortcuts, rest } = splitCategories(home.categories, SHORTCUT_CATEGORY_SLUGS);
  const hasContact = contactFields(home.company, locale).length > 0 || (home.company.social_links?.length ?? 0) > 0;
  return (
    <main className="space-y-10 sm:space-y-12">
      <section className="relative overflow-hidden rounded-2xl bg-navy text-white shadow-card">
        {/* Soft teal accents recovered from the prior navy+teal system (#0D9488). */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_100%_0%,rgba(13,148,136,0.32),transparent_55%)]"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_0%_100%,rgba(13,148,136,0.14),transparent_50%)]"
        />
        <div className="relative z-10 grid items-center gap-6 px-5 py-7 sm:px-8 sm:py-9 lg:grid-cols-[minmax(0,1.15fr)_minmax(16rem,20rem)] lg:gap-8 lg:px-10">
          <div className="relative z-20 min-w-0">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/80">
              <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 bg-teal shadow-[0_0_0_3px_rgba(13,148,136,0.35)]" />
              {home.company.name}
            </p>
            <h1 className="mt-3 max-w-xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
              {text.heroHeadline}
            </h1>
            <p className="mt-3 max-w-xl text-base leading-7 text-white/80">{text.heroText}</p>
            <div className="mt-5">
              <HomeSearch locale={locale} />
            </div>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <Link href={`/${locale}/catalog`} className="btn-on-dark">
                {text.browseCatalog}
              </Link>
              <Link href={`/${locale}/contact`} className="btn-ghost">
                {text.contact}
              </Link>
            </div>
          </div>
          <div className="relative z-0 min-w-0">
            {hero?.image ? (
              <HomeHeroProduct product={hero} locale={locale} />
            ) : (
              <div className="rounded-xl bg-mist px-4 py-6 text-navy">
                <CameraFigure />
              </div>
            )}
          </div>
        </div>
        <div aria-hidden="true" className="relative z-10 h-1 bg-gradient-to-r from-brand via-sky to-teal" />
      </section>
      <section className="space-y-5" aria-labelledby="categories-heading">
        <SectionHeading
          id="categories-heading"
          title={text.categories}
          intro={text.categoryIntro}
          href={`/${locale}/categories`}
          action={text.allCategories}
        />
        {shortcuts.length ? (
          <ul className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 lg:grid-cols-4">
            {shortcuts.map((category) => (
              <li key={category.slug} className="min-w-0">
                <HomeCategoryCard category={category} locale={locale} />
              </li>
            ))}
          </ul>
        ) : home.categories.length ? (
          <CategoryGrid categories={home.categories} locale={locale} />
        ) : (
          <CategoryEmpty title={text.homeEmptyCategoriesTitle} body={text.homeEmptyCategories} href={`/${locale}/catalog`} action={text.browseCatalog} />
        )}
      </section>
      <section className="space-y-5" aria-labelledby="products-heading">
        <SectionHeading
          id="products-heading"
          title={text.products}
          intro={featured.length ? text.featuredIntro : text.productIntro}
          href={`/${locale}/catalog`}
          action={text.catalog}
        />
        {shown.length ? (
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
      {rest.length ? (
        <section className="space-y-4" aria-labelledby="more-categories-heading">
          <div className="flex items-end justify-between gap-4 border-b border-line pb-3">
            <h2 id="more-categories-heading" className="text-lg font-semibold tracking-tight text-ink">
              {text.otherSections}
            </h2>
            <Link href={`/${locale}/categories`} className={`shrink-0 text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
              {text.allCategories}
            </Link>
          </div>
          <ul className="flex flex-wrap gap-2">
            {rest.map((category) => (
              <li key={category.slug}>
                <Link
                  href={categoryPath(locale, category.slug, null)}
                  className={`inline-flex min-h-11 items-center gap-2 rounded-lg border border-line bg-white px-3 text-sm font-medium text-ink transition hover:border-brand hover:text-brand ${focusLight}`}
                >
                  {category.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <HomeLandingSections locale={locale} categories={home.categories} company={home.company} />
      {!hasContact ? (
        <section className="surface-card p-6 sm:flex sm:items-center sm:justify-between sm:gap-8 sm:p-8" aria-labelledby="about-heading">
          <div>
            <div aria-hidden="true" className="accent-rail mb-3" />
            <h2 id="about-heading" className="text-2xl font-semibold tracking-tight text-ink">
              {home.company.name}
            </h2>
          </div>
          <Link href={`/${locale}/contact`} className="btn-primary mt-5 sm:mt-0">
            {text.contact}
          </Link>
        </section>
      ) : null}
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

function CategoryGrid({ categories, locale }: { categories: CategoryNode[]; locale: PublicLocale }) {
  return (
    <ul className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 lg:grid-cols-4">
      {categories.map((category) => (
        <li key={category.slug} className="min-w-0">
          <HomeCategoryCard category={category} locale={locale} />
        </li>
      ))}
    </ul>
  );
}

function SectionHeading({
  id,
  title,
  intro,
  href,
  action,
}: {
  id: string;
  title: string;
  intro: string;
  href: string;
  action: string;
}) {
  return (
    <div className="flex items-end justify-between gap-4 border-b border-line pb-4">
      <div>
        <div aria-hidden="true" className="accent-rail mb-2" />
        <h2 id={id} className="text-2xl font-semibold tracking-tight text-ink">
          {title}
        </h2>
        <p className="mt-1 text-sm text-mute">{intro}</p>
      </div>
      <Link href={href} className={`shrink-0 text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
        {action}
      </Link>
    </div>
  );
}

function CategoryEmpty({ title, body, href, action }: { title: string; body: string; href: string; action: string }) {
  return (
    <div role="status" className="flex flex-col gap-4 surface-card p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
      <div className="flex items-start gap-4">
        <span className="grid h-12 w-12 shrink-0 place-items-center rounded-lg bg-mist text-brand">
          <FolderGlyph />
        </span>
        <div>
          <p className="font-semibold text-ink">{title}</p>
          <p className="mt-1 max-w-xl text-sm leading-6 text-mute">{body}</p>
        </div>
      </div>
      <Link href={href} className="btn-secondary shrink-0">
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
