import type { Metadata } from "next";
import Link from "next/link";

import { AccentBar, CameraFigure, CameraGlyph, FolderGlyph, focusLight } from "@/components/public/brand-mark";
import { ContactDetails } from "@/components/public/contact-details";
import { JsonLd } from "@/components/public/json-ld";
import { ProductCard } from "@/components/public/product-card";
import { loadPublic, requireLocale, type CategoryNode, type Company, type PublicCard } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
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
  return (
    <main className="space-y-12 sm:space-y-14">
      <JsonLd data={organizationJson(home.company)} />
      <JsonLd data={websiteJson(locale, home.company.name || SITE_NAME)} />
      <section className="overflow-hidden rounded-md bg-white shadow-sm ring-1 ring-navy/10">
        <AccentBar />
        <div className="grid lg:grid-cols-[minmax(0,1.4fr)_minmax(18rem,0.9fr)]">
          <div className="grid gap-6 px-6 py-8 sm:grid-cols-[minmax(0,1fr)_11rem] sm:items-stretch sm:gap-8 sm:px-8 sm:py-10 lg:px-10 lg:py-12">
            <div className="min-w-0">
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand">
                <span aria-hidden="true" className="h-1.5 w-1.5 bg-teal" />
                {home.company.name}
              </p>
              <h1 className="mt-4 max-w-xl text-4xl font-semibold tracking-tight text-navy sm:text-5xl sm:leading-[1.05]">
                {text.heroHeadline}
              </h1>
              <p className="mt-4 max-w-xl text-base leading-7 text-navy/70">{text.heroText}</p>
              <div className="mt-7 flex flex-col gap-3 sm:flex-row">
                <Link
                  href={`/${locale}/catalog`}
                  className={`inline-flex min-h-11 items-center justify-center bg-brand px-5 text-sm font-medium text-white hover:bg-navy ${focusLight}`}
                >
                  {text.browseCatalog}
                </Link>
                <Link
                  href={`/${locale}/contact`}
                  className={`inline-flex min-h-11 items-center justify-center border border-brand bg-white px-5 text-sm font-medium text-brand hover:bg-mist ${focusLight}`}
                >
                  {text.contact}
                </Link>
              </div>
            </div>
            <div className="flex items-center justify-center overflow-hidden bg-mist px-4 py-6">
              <CameraFigure />
            </div>
          </div>
          <div className="flex flex-col justify-center border-t border-navy/10 bg-mist px-6 py-8 sm:px-8 lg:border-l lg:border-t-0 lg:py-12">
            <form action={`/${locale}/search`} method="get" role="search" className="flex h-full flex-col justify-center gap-4">
              <div className="space-y-1">
                <label htmlFor="home-search" className="text-sm font-semibold text-navy">
                  {text.searchCatalog}
                </label>
                <p className="text-sm text-navy/70">{text.searchPlaceholder}</p>
              </div>
              <input
                id="home-search"
                name="q"
                type="search"
                maxLength={80}
                placeholder={text.searchPlaceholder}
                className="min-h-11 w-full border border-navy/15 bg-white px-3 text-navy placeholder:text-navy/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
              />
              <button
                type="submit"
                className="inline-flex min-h-11 w-full items-center justify-center bg-brand px-5 text-sm font-medium text-white hover:bg-navy focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
              >
                {text.search}
              </button>
            </form>
          </div>
        </div>
      </section>
      <section className="space-y-5" aria-labelledby="categories-heading">
        <SectionHeading
          id="categories-heading"
          title={text.categories}
          intro={text.categoryIntro}
          href={`/${locale}/categories`}
          action={text.categories}
        />
        {home.categories.length ? (
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {home.categories.map((category) => (
              <li key={category.slug}>
                <Link
                  href={`/${locale}/categories/${category.slug}`}
                  className={`group flex h-full flex-col overflow-hidden rounded-md border border-navy/10 bg-white shadow-sm transition hover:border-brand hover:shadow-md ${focusLight}`}
                >
                  <span aria-hidden="true" className="h-1 bg-brand transition group-hover:bg-teal" />
                  <span className="flex flex-1 flex-col p-5">
                    <span className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">{text.category}</span>
                    <span className="mt-3 text-lg font-semibold text-navy group-hover:text-brand">{category.name}</span>
                    {category.translation_fallback ? <span className="mt-2 text-sm text-navy/60">{text.fallback}</span> : null}
                    {category.description ? <span className="mt-3 text-sm leading-6 text-navy/70">{category.description}</span> : null}
                    <span className="mt-auto block pt-6">
                      <span className="inline-flex bg-mist px-2.5 py-1 text-sm text-navy/80">
                        {text.products}: {category.product_count}
                      </span>
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <CategoryEmpty title={text.homeEmptyCategoriesTitle} body={text.homeEmptyCategories} href={`/${locale}/catalog`} action={text.browseCatalog} />
        )}
      </section>
      <section className="space-y-5" aria-labelledby="products-heading">
        <SectionHeading
          id="products-heading"
          title={text.products}
          intro={text.productIntro}
          href={`/${locale}/catalog`}
          action={text.catalog}
        />
        {home.products.length ? (
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {home.products.map((product) => (
              <li key={product.slug}>
                <ProductCard product={product} locale={locale} />
              </li>
            ))}
          </ul>
        ) : (
          <ProductEmpty title={text.homeEmptyProductsTitle} body={text.homeEmptyProducts} href={`/${locale}/catalog`} action={text.browseCatalog} />
        )}
      </section>
      <ContactDetails company={home.company} locale={locale} />
    </main>
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
