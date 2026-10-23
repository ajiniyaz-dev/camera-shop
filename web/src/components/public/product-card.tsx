import Link from "next/link";

import { CameraGlyph, focusLight } from "@/components/public/brand-mark";
import { ProductPhoto } from "@/components/public/product-photo";
import { PriceLabel } from "@/components/public/price-label";
import { SelectionButton } from "@/components/public/selection-button";
import { billingPeriod, isServicePlan, showOriginalNote } from "@/lib/presentation";
import { categoryPath, type PublicCard } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function ProductCard({ product, locale }: { product: PublicCard; locale: PublicLocale }) {
  const text = messages[locale];
  const period = billingPeriod(product.option_label);
  const categoryHref = product.category
    ? categoryPath(locale, product.category.slug, product.category.parent_slug)
    : null;
  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-lg border border-line bg-white transition duration-200 hover:border-brand/40 motion-reduce:transition-none">
      {product.image ? (
        <Link
          href={`/${locale}/products/${product.slug}`}
          className={`flex h-32 w-full items-center justify-center bg-mist ${focusLight}`}
        >
          <ProductPhoto src={product.image.url} alt={product.image.alt} width={product.image.width} height={product.image.height} />
        </Link>
      ) : (
        <Link
          href={`/${locale}/products/${product.slug}`}
          className={`flex h-32 flex-col items-center justify-center gap-1 bg-mist px-3 text-center text-xs text-mute ${focusLight}`}
        >
          <CameraGlyph className="h-7 w-7 text-navy" />
          {text.noImage}
        </Link>
      )}
      <div className="flex flex-1 flex-col gap-1.5 p-3">
        {isServicePlan(product) ? (
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-teal">{text.service}</p>
        ) : null}
        <h2 className="line-clamp-2 text-base font-semibold leading-snug text-ink">
          <Link href={`/${locale}/products/${product.slug}`} className={`underline-offset-2 hover:text-brand hover:underline ${focusLight}`}>
            {product.name || product.model_display}
          </Link>
        </h2>
        {showOriginalNote(product.translation_fallback, product.name) ? (
          <p className="text-xs text-mute">{text.fallback}</p>
        ) : null}
        <p className="truncate font-mono text-sm text-ink/80" title={`${text.model}: ${product.model_display}`}>
          {product.model_display}
          {!period && product.option_label ? ` · ${product.option_label}` : ""}
        </p>
        {period ? (
          <p className="truncate text-sm text-mute">
            {text.billing}: {period === "monthly" ? text.billingMonthly : text.billingYearly}
          </p>
        ) : null}
        {product.category && categoryHref ? (
          <Link href={categoryHref} className={`truncate text-sm text-mute underline-offset-2 hover:text-brand hover:underline ${focusLight}`}>
            {product.category.name}
          </Link>
        ) : product.brand ? (
          <p className="truncate text-sm text-mute">{product.brand.name}</p>
        ) : null}
        <div className="mt-auto space-y-2 border-t border-line pt-2">
          <PriceLabel price={product.price} locale={locale} compact />
          {product.out_of_stock ? <p className="text-xs font-medium text-red-800">{text.outOfStock}</p> : null}
          <SelectionButton slug={product.slug} locale={locale} compact />
        </div>
      </div>
    </article>
  );
}
