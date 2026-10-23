import type { Metadata } from "next";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { focusLight } from "@/components/public/brand-mark";
import { JsonLd } from "@/components/public/json-ld";
import { ProductDescriptionBlock } from "@/components/public/product-description-block";
import { ProductDetailInfo } from "@/components/public/product-detail-info";
import { ProductGallery } from "@/components/public/product-gallery";
import { ProductSpecTable } from "@/components/public/product-spec-table";
import { descriptionParagraphs } from "@/lib/product-description";
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
  const crumbs = [
    { name: text.home, path: `/${locale}` },
    { name: text.catalog, path: `/${locale}/catalog` },
    ...(product.category?.breadcrumb ?? []).map((item) => ({
      name: item.name,
      path: categoryPath(locale, item.slug, item.parent_slug),
    })),
    { name: product.name, path: `/${locale}/products/${product.slug}` },
  ];
  const description = descriptionParagraphs(product.description).length ? product.description : null;
  const specifications = product.specifications.filter((spec) => spec.name.trim() && spec.value.trim());
  const showContentNav = Boolean(description && specifications.length);
  return (
    <main className="space-y-4">
      <JsonLd data={breadcrumbJson(crumbs)} />
      <JsonLd data={productJson(product)} />
      <Breadcrumbs label={text.navigation} items={crumbs} compact />
      <div className="overflow-hidden rounded-lg border border-line bg-white">
        <div className="grid md:grid-cols-[minmax(0,1.15fr)_minmax(17rem,22rem)] lg:grid-cols-[minmax(0,1fr)_minmax(20rem,24rem)]">
          <div className="min-w-0 border-b border-line bg-mist md:border-b-0 md:border-r">
            <ProductGallery images={product.images} emptyLabel={text.noImage} label={text.images} />
          </div>
          <ProductDetailInfo product={product} locale={locale} />
        </div>
      </div>
      {description || specifications.length ? (
        <div className="space-y-4">
          {showContentNav ? (
            <nav className="flex gap-5 border-b border-line text-sm font-medium" aria-label={`${text.description}, ${text.specifications}`}>
              <a
                href="#product-description"
                className={`border-b-2 border-transparent pb-2 text-navy hover:border-teal hover:text-brand ${focusLight}`}
              >
                {text.description}
              </a>
              <a
                href="#product-specifications"
                className={`border-b-2 border-transparent pb-2 text-navy hover:border-teal hover:text-brand ${focusLight}`}
              >
                {text.specifications}
              </a>
            </nav>
          ) : null}
          {description ? (
            <ProductDescriptionBlock
              id="product-description"
              title={text.description}
              text={description}
              showFallback={product.description_fallback}
              fallbackLabel={text.fallback}
            />
          ) : null}
          <ProductSpecTable
            id="product-specifications"
            title={text.specifications}
            fallbackLabel={text.fallback}
            specifications={specifications}
          />
        </div>
      ) : null}
    </main>
  );
}
