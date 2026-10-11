import Link from "next/link";

import { PriceLabel } from "@/components/public/price-label";
import { categoryPath, publicGetOrNotFound, requireLocale, type PublicDetail } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";

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
  return (
    <main className="space-y-8">
      <nav aria-label={text.categories} className="text-sm text-slate-700">
        <ol className="flex flex-wrap gap-2">
          <li>
            <Link href={`/${locale}/catalog`} className="underline underline-offset-4">
              {text.catalog}
            </Link>
          </li>
          {product.category?.breadcrumb.map((item) => (
            <li key={`${item.parent_slug ?? ""}/${item.slug}`}>
              <span aria-hidden="true">/</span>{" "}
              <Link href={categoryPath(locale, item.slug, item.parent_slug)} className="underline underline-offset-4">
                {item.name}
              </Link>
            </li>
          ))}
        </ol>
      </nav>
      <div className="grid gap-8 lg:grid-cols-2">
        <section className="space-y-3">
          {product.images.length ? (
            <ul className="space-y-3">
              {product.images.map((image) => (
                <li key={image.url} className="overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
                  <img
                    src={image.url}
                    alt={image.alt}
                    width={image.width ?? 960}
                    height={image.height ?? 720}
                    className="h-auto max-h-[32rem] w-full object-contain"
                  />
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex h-72 items-center justify-center rounded-lg bg-slate-100 text-slate-700">{text.noImage}</div>
          )}
        </section>
        <section className="space-y-4">
          <h1 className="text-3xl font-semibold leading-tight">{product.name}</h1>
          {product.translation_fallback ? <p className="text-sm text-slate-600">{text.fallback}</p> : null}
          <p>
            {text.model}: {product.model_display}
            {product.option_label ? ` · ${product.option_label}` : ""}
          </p>
          {product.brand ? (
            <p>
              {text.brand}:{" "}
              <Link href={`/${locale}/brands/${product.brand.slug}`} className="underline underline-offset-4">
                {product.brand.name}
              </Link>
            </p>
          ) : null}
          {product.category ? (
            <p>
              {text.category}:{" "}
              <Link
                href={categoryPath(locale, product.category.slug, product.category.parent_slug)}
                className="underline underline-offset-4"
              >
                {product.category.name}
              </Link>
            </p>
          ) : null}
          <PriceLabel price={product.price} locale={locale} />
          {product.out_of_stock ? <p className="font-medium text-red-800">{text.outOfStock}</p> : null}
          <p>
            <Link href={`/${locale}/catalog`} className="underline underline-offset-4">
              {text.backToCatalog}
            </Link>
          </p>
        </section>
      </div>
      {product.description ? (
        <section className="max-w-3xl space-y-2">
          <h2 className="text-xl font-semibold">{text.description}</h2>
          {product.description_fallback ? <p className="text-sm text-slate-600">{text.fallback}</p> : null}
          <p className="whitespace-pre-wrap leading-7">{product.description}</p>
        </section>
      ) : null}
      {product.specifications.length ? (
        <section className="space-y-3">
          <h2 className="text-xl font-semibold">{text.specifications}</h2>
          <table className="w-full border-collapse text-left text-sm">
            <tbody>
              {product.specifications.map((spec) => (
                <tr key={`${spec.name}-${spec.value}`} className="border-t border-slate-200">
                  <th scope="row" className="w-1/3 py-3 pr-4 font-medium">
                    {spec.name}
                    {spec.translation_fallback ? <span className="mt-1 block text-xs font-normal text-slate-600">{text.fallback}</span> : null}
                  </th>
                  <td className="py-3">{spec.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </main>
  );
}
