import type { Metadata } from "next";
import Link from "next/link";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { focusLight } from "@/components/public/brand-mark";
import { ModelMetaIcon } from "@/components/public/catalog-icons";
import { CatalogLinks } from "@/components/public/catalog-links";
import { JsonLd } from "@/components/public/json-ld";
import { PriceLabel } from "@/components/public/price-label";
import { ProductGallery } from "@/components/public/product-gallery";
import { SelectionButton } from "@/components/public/selection-button";
import { billingPeriod, isServicePlan, showOriginalNote } from "@/lib/presentation";
import { categoryPath, publicGetOrNotFound, requireLocale, type PublicDetail } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
import { breadcrumbJson, pageMetadata, productDescription, productJson, productTitle } from "@/lib/seo";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const locale = await requireLocale(params);
  const product = await publicGetOrNotFound<PublicDetail>(
    `/api/public/products/${encodeURIComponent(slug)}?locale=${locale}`,
  );
  return pageMetadata({
    locale,
    title: productTitle(product),
    description: productDescription(product),
    path: `/${locale}/products/${slug}`,
    index: true,
    image: product.images[0] ?? null,
  });
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { slug } = await params;
  const locale = await requireLocale(params);
  const text = messages[locale];
  const product = await publicGetOrNotFound<PublicDetail>(
    `/api/public/products/${encodeURIComponent(slug)}?locale=${locale}`,
  );
  const period = billingPeriod(product.option_label);
  const crumbs = [
    { name: text.home, path: `/${locale}` },
    { name: text.catalog, path: `/${locale}/catalog` },
    ...(product.category?.breadcrumb ?? []).map((item) => ({
      name: item.name,
      path: categoryPath(locale, item.slug, item.parent_slug),
    })),
    { name: product.name, path: `/${locale}/products/${product.slug}` },
  ];
  return (
    <main className="space-y-10">
      <JsonLd data={breadcrumbJson(crumbs)} />
      <JsonLd data={productJson(product)} />
      <Breadcrumbs label={text.navigation} items={crumbs} />
      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)]">
        <ProductGallery images={product.images} emptyLabel={text.noImage} label={text.images} />
        <section className="space-y-4 border border-navy/10 bg-white p-6 shadow-sm">
          {isServicePlan(product) ? <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal">{text.service}</p> : null}
          <h1 className="text-3xl font-semibold leading-tight tracking-tight text-navy">{product.name}</h1>
          {showOriginalNote(product.translation_fallback, product.name) ? <p className="text-sm text-navy/60">{text.fallback}</p> : null}
          <p className="flex items-start gap-2 text-sm text-navy/80">
            <ModelMetaIcon />
            <span className="min-w-0">
              {text.model}: {product.model_display}
              {!period && product.option_label ? ` · ${product.option_label}` : ""}
            </span>
          </p>
          {period ? (
            <p className="pl-[1.375rem] text-sm text-navy/80">
              {text.billing}: {period === "monthly" ? text.billingMonthly : text.billingYearly}
            </p>
          ) : null}
          <CatalogLinks locale={locale} brand={product.brand} category={product.category} />
          <div className="border-t border-navy/10 pt-4">
            <PriceLabel price={product.price} locale={locale} />
          </div>
          {product.out_of_stock ? <p className="text-sm font-medium text-red-800">{text.outOfStock}</p> : null}
          <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:flex-wrap">
            <SelectionButton slug={product.slug} locale={locale} />
            <Link
              href={`/${locale}/contact`}
              className={`inline-flex min-h-11 items-center justify-center bg-brand px-5 text-sm font-medium text-white hover:bg-navy ${focusLight}`}
            >
              {text.contact}
            </Link>
            <Link
              href={`/${locale}/catalog`}
              className={`inline-flex min-h-11 items-center justify-center border border-brand px-5 text-sm font-medium text-brand hover:bg-mist ${focusLight}`}
            >
              {text.backToCatalog}
            </Link>
          </div>
        </section>
      </div>
      {product.description ? (
        <section className="max-w-3xl space-y-3">
          <h2 className="text-xl font-semibold tracking-tight text-navy">{text.description}</h2>
          {product.description_fallback ? <p className="text-sm text-navy/60">{text.fallback}</p> : null}
          <p className="whitespace-pre-wrap leading-7 text-navy/80">{product.description}</p>
        </section>
      ) : null}
      {product.specifications.length ? (
        <section className="space-y-3">
          <h2 className="text-xl font-semibold tracking-tight text-navy">{text.specifications}</h2>
          <div className="overflow-x-auto border border-navy/10 bg-white">
            <table className="w-full min-w-[20rem] border-collapse text-left text-sm">
              <tbody>
                {product.specifications.map((spec) => (
                  <tr key={`${spec.name}-${spec.value}`} className="border-t border-navy/10">
                    <th scope="row" className="w-2/5 bg-mist px-4 py-3 font-medium text-navy">
                      {spec.name}
                      {showOriginalNote(spec.translation_fallback, spec.name) ? <span className="mt-1 block text-xs font-normal text-navy/60">{text.fallback}</span> : null}
                    </th>
                    <td className="px-4 py-3 text-navy/80">{spec.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </main>
  );
}
