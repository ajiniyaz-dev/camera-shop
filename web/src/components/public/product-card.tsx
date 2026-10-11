import Link from "next/link";

import { PriceLabel } from "@/components/public/price-label";
import { categoryPath, type PublicCard } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function ProductCard({ product, locale }: { product: PublicCard; locale: PublicLocale }) {
  const text = messages[locale];
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-lg border border-slate-200 bg-white">
      {product.image ? (
        <img
          src={product.image.url}
          alt={product.image.alt}
          width={product.image.width ?? 640}
          height={product.image.height ?? 480}
          className="h-48 w-full bg-slate-50 object-contain"
        />
      ) : (
        <div className="flex h-48 items-center justify-center bg-slate-100 px-4 text-center text-sm text-slate-700">
          {text.noImage}
        </div>
      )}
      <div className="flex flex-1 flex-col gap-2 p-4">
        <h2 className="text-lg font-semibold leading-snug">
          <Link
            href={`/${locale}/products/${product.slug}`}
            className="rounded underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-800"
          >
            {product.name}
          </Link>
        </h2>
        {product.translation_fallback ? <p className="text-sm text-slate-600">{text.fallback}</p> : null}
        <p className="text-sm text-slate-700">
          {text.model}: {product.model_display}
          {product.option_label ? ` · ${product.option_label}` : ""}
        </p>
        {product.brand ? (
          <p className="text-sm">
            <Link className="underline underline-offset-4" href={`/${locale}/brands/${product.brand.slug}`}>
              {product.brand.name}
            </Link>
          </p>
        ) : null}
        {product.category ? (
          <p className="text-sm">
            <Link
              className="underline underline-offset-4"
              href={categoryPath(locale, product.category.slug, product.category.parent_slug)}
            >
              {product.category.name}
            </Link>
          </p>
        ) : null}
        <PriceLabel price={product.price} locale={locale} />
        {product.out_of_stock ? <p className="text-sm font-medium text-red-800">{text.outOfStock}</p> : null}
      </div>
    </article>
  );
}
