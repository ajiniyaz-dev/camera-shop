import Link from "next/link";

import { CameraGlyph, focusLight } from "@/components/public/brand-mark";
import { ModelMetaIcon } from "@/components/public/catalog-icons";
import { CatalogLinks } from "@/components/public/catalog-links";
import { ProductPhoto } from "@/components/public/product-photo";
import { PriceLabel } from "@/components/public/price-label";
import { SelectionButton } from "@/components/public/selection-button";
import { billingPeriod, isServicePlan, showOriginalNote } from "@/lib/presentation";
import type { PublicCard } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function ProductCard({ product, locale }: { product: PublicCard; locale: PublicLocale }) {
  const text = messages[locale];
  const period = billingPeriod(product.option_label);
  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-md border border-navy/10 bg-white shadow-sm transition hover:border-brand hover:shadow-md">
      <div aria-hidden="true" className="h-1 bg-brand transition group-hover:bg-teal" />
      {product.image ? (
        <span className="flex h-52 w-full items-center justify-center border-b border-navy/10 bg-mist">
          <ProductPhoto src={product.image.url} alt={product.image.alt} width={product.image.width} height={product.image.height} />
        </span>
      ) : (
        <div className="flex h-52 flex-col items-center justify-center gap-3 border-b border-navy/10 bg-mist px-4 text-center text-sm text-navy/70">
          <CameraGlyph className="h-10 w-10 text-navy" />
          {text.noImage}
        </div>
      )}
      <div className="flex flex-1 flex-col gap-3 p-5">
        {isServicePlan(product) ? <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal">{text.service}</p> : null}
        <h2 className="line-clamp-2 min-h-[2.75rem] text-lg font-semibold leading-snug text-navy">
          <Link href={`/${locale}/products/${product.slug}`} className={`underline-offset-4 hover:text-brand hover:underline ${focusLight}`}>
            {product.name}
          </Link>
        </h2>
        {showOriginalNote(product.translation_fallback, product.name) ? <p className="text-sm text-navy/60">{text.fallback}</p> : null}
        <p className="flex items-start gap-2 text-sm text-navy/70">
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
        <div className="mt-auto space-y-3 border-t border-navy/10 pt-4">
          <PriceLabel price={product.price} locale={locale} />
          <SelectionButton slug={product.slug} locale={locale} />
        </div>
        {product.out_of_stock ? <p className="text-sm font-medium text-red-800">{text.outOfStock}</p> : null}
      </div>
    </article>
  );
}
