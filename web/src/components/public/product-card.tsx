import Link from "next/link";

import { CameraGlyph, focusLight } from "@/components/public/brand-mark";
import { PriceLabel } from "@/components/public/price-label";
import { categoryPath, type PublicCard } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function ProductCard({ product, locale }: { product: PublicCard; locale: PublicLocale }) {
  const text = messages[locale];
  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-md border border-navy/10 bg-white shadow-sm transition hover:border-brand hover:shadow-md">
      <div aria-hidden="true" className="h-1 bg-brand transition group-hover:bg-teal" />
      {product.image ? (
        <img
          src={product.image.url}
          alt={product.image.alt}
          width={product.image.width ?? 640}
          height={product.image.height ?? 480}
          className="h-52 w-full border-b border-navy/10 bg-mist object-contain"
        />
      ) : (
        <div className="flex h-52 flex-col items-center justify-center gap-3 border-b border-navy/10 bg-mist px-4 text-center text-sm text-navy/70">
          <CameraGlyph className="h-10 w-10 text-navy" />
          {text.noImage}
        </div>
      )}
      <div className="flex flex-1 flex-col gap-2 p-5">
        <h2 className="text-lg font-semibold leading-snug text-navy">
          <Link href={`/${locale}/products/${product.slug}`} className={`underline-offset-4 hover:text-brand hover:underline ${focusLight}`}>
            {product.name}
          </Link>
        </h2>
        {product.translation_fallback ? <p className="text-sm text-navy/60">{text.fallback}</p> : null}
        <p className="text-sm text-navy/70">
          {text.model}: {product.model_display}
          {product.option_label ? ` · ${product.option_label}` : ""}
        </p>
        {product.brand ? (
          <p className="text-sm">
            <Link className={`text-brand underline-offset-4 hover:underline ${focusLight}`} href={`/${locale}/brands/${product.brand.slug}`}>
              {product.brand.name}
            </Link>
          </p>
        ) : null}
        {product.category ? (
          <p className="text-sm">
            <Link
              className={`text-brand underline-offset-4 hover:underline ${focusLight}`}
              href={categoryPath(locale, product.category.slug, product.category.parent_slug)}
            >
              {product.category.name}
            </Link>
          </p>
        ) : null}
        <div className="mt-auto border-t border-navy/10 pt-3">
          <PriceLabel price={product.price} locale={locale} />
        </div>
        {product.out_of_stock ? <p className="text-sm font-medium text-red-800">{text.outOfStock}</p> : null}
      </div>
    </article>
  );
}
