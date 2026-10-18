import type { Metadata } from "next";
import Link from "next/link";

import { CameraFigure, CameraGlyph, FolderGlyph, focusLight } from "@/components/public/brand-mark";
import { contactFields, ContactDetails } from "@/components/public/contact-details";
import { HomeCategoryCard, HomeHeroProduct, HomeProductCard } from "@/components/public/home-cards";
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
      <section className="rounded-md bg-navy text-white shadow-sm">
        <div className="grid items-center gap-6 px-5 py-7 sm:px-8 sm:py-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(16rem,20rem)] lg:gap-8 lg:px-10">
          <div className="relative z-20 min-w-0">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/80">
              <span aria-hidden="true" className="h-1.5 w-1.5 bg-teal" />
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
              <Link
                href={`/${locale}/catalog`}
                className="inline-flex min-h-11 items-center justify-center bg-white px-5 text-sm font-medium text-navy hover:bg-mist focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                {text.browseCatalog}
              </Link>
              <Link
                href={`/${locale}/contact`}
                className="inline-flex min-h-11 items-center justify-center border border-white/50 px-5 text-sm font-medium text-white hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                {text.contact}
              </Link>
            </div>
          </div>
          <div className="relative z-0 min-w-0">
            {hero?.image ? (
              <HomeHeroProduct product={hero} locale={locale} />
            ) : (
              <div className="rounded-md bg-mist px-4 py-6 text-navy">
                <CameraFigure />
              </div>
            )}
          </div>
        </div>
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
          <div className="flex items-end justify-between gap-4 border-b border-navy/10 pb-3">
            <h2 id="more-categories-heading" className="text-lg font-semibold tracking-tight text-navy">
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
                  className={`inline-flex min-h-11 items-center gap-2 rounded-md border border-navy/10 bg-white px-3 text-sm font-medium text-navy hover:border-brand hover:text-brand ${focusLight}`}
                >
                  {category.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {hasContact ? (
        <ContactDetails company={home.company} locale={locale} />
      ) : (
        <section className="rounded-md border border-navy/10 bg-white p-6 shadow-sm sm:flex sm:items-center sm:justify-between sm:gap-8 sm:p-8" aria-labelledby="about-heading">
          <div>
            <div aria-hidden="true" className="mb-3 h-1 w-8 bg-teal" />
            <h2 id="about-heading" className="text-2xl font-semibold tracking-tight text-navy">
              {home.company.name}
            </h2>
          </div>
          <Link
            href={`/${locale}/contact`}
            className={`mt-5 inline-flex min-h-11 shrink-0 items-center justify-center bg-brand px-5 text-sm font-medium text-white hover:bg-navy sm:mt-0 ${focusLight}`}
          >
            {text.contact}
          </Link>
        </section>
      )}
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
    <div className="flex items-end justify-between gap-4 border-b border-navy/10 pb-4">
      <div>
        <div aria-hidden="true" className="mb-2 h-1 w-8 bg-teal" />
        <h2 id={id} className="text-2xl font-semibold tracking-tight text-navy">
          {title}
        </h2>
        <p className="mt-1 text-sm text-navy/70">{intro}</p>
      </div>
      <Link href={href} className={`shrink-0 text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
        {action}
      </Link>
    </div>
  );
}

function CategoryEmpty({ title, body, href, action }: { title: string; body: string; href: string; action: string }) {
  return (
    <div role="status" className="flex flex-col gap-4 rounded-md border border-navy/10 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between sm:p-6">
      <div className="flex items-start gap-4">
        <span className="grid h-12 w-12 shrink-0 place-items-center bg-mist text-brand">
          <FolderGlyph />
        </span>
        <div>
          <p className="font-semibold text-navy">{title}</p>
          <p className="mt-1 max-w-xl text-sm leading-6 text-navy/70">{body}</p>
        </div>
      </div>
      <Link
        href={href}
        className={`inline-flex min-h-11 shrink-0 items-center justify-center border border-brand px-4 text-sm font-medium text-brand hover:bg-mist ${focusLight}`}
      >
        {action}
      </Link>
    </div>
  );
}

function ProductEmpty({ title, body, href, action }: { title: string; body: string; href: string; action: string }) {
  return (
    <div role="status" className="flex flex-col gap-4 rounded-md border border-brand/25 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:p-6">
      <span className="grid h-14 w-14 shrink-0 place-items-center bg-navy text-white">
        <CameraGlyph className="h-8 w-8" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-navy">{title}</p>
        <p className="mt-1 max-w-xl text-sm leading-6 text-navy/70">{body}</p>
      </div>
      <Link
        href={href}
        className={`inline-flex min-h-11 shrink-0 items-center justify-center bg-brand px-4 text-sm font-medium text-white hover:bg-navy ${focusLight}`}
      >
        {action}
      </Link>
    </div>
  );
}
