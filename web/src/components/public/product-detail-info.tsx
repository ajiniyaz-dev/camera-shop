import Link from "next/link";

import { focusLight } from "@/components/public/brand-mark";
import { BackLinkIcon, ContactActionIcon, ModelMetaIcon } from "@/components/public/catalog-icons";
import { CatalogLinks } from "@/components/public/catalog-links";
import { PriceLabel } from "@/components/public/price-label";
import { ProductDescriptionPreview } from "@/components/public/product-description-preview";
import { SelectionButton } from "@/components/public/selection-button";
import { billingPeriod, isServicePlan, showOriginalNote } from "@/lib/presentation";
import type { PublicDetail } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

const metaIcon = "h-3.5 w-3.5 shrink-0 text-mute";

export function ProductDetailInfo({
  product,
  locale,
}: {
  product: PublicDetail;
  locale: PublicLocale;
}) {
  const text = messages[locale];
  const period = billingPeriod(product.option_label);
  return (
    <section className="flex h-full min-w-0 flex-col p-5 sm:p-6">
      {isServicePlan(product) ? (
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-teal">{text.service}</p>
      ) : null}
      <h1 className="break-words text-xl font-semibold leading-snug tracking-tight text-navy sm:text-2xl">{product.name}</h1>
      {showOriginalNote(product.translation_fallback, product.name) ? (
        <p className="mt-1 text-sm text-mute">{text.fallback}</p>
      ) : null}
      <div className="mt-3 space-y-1.5 text-sm">
        <p className="flex items-start gap-2 text-ink/85">
          <ModelMetaIcon className={`${metaIcon} mt-0.5`} />
          <span className="min-w-0 break-words">
            <span className="text-navy/65">{text.model}: </span>
            <span className="font-mono text-[13px]">{product.model_display}</span>
            {!period && product.option_label ? ` · ${product.option_label}` : ""}
          </span>
        </p>
        {period ? (
          <p className="pl-[1.375rem] text-ink/80">
            {text.billing}: {period === "monthly" ? text.billingMonthly : text.billingYearly}
          </p>
        ) : null}
        <CatalogLinks locale={locale} brand={product.brand} category={product.category} />
      </div>
      <div className="mt-4 border-t border-line pt-4">
        <PriceLabel price={product.price} locale={locale} featured />
        {product.out_of_stock ? <p className="mt-2 text-sm font-medium text-red-800">{text.outOfStock}</p> : null}
        <ProductDescriptionPreview
          description={product.description}
          readMoreLabel={text.readMore}
          showLessLabel={text.showLess}
        />
      </div>
      <div className="mt-4 flex flex-col gap-2">
        <SelectionButton slug={product.slug} locale={locale} stretch />
        <Link href={`/${locale}/contact`} className="btn-secondary w-full">
          <ContactActionIcon />
          {text.contact}
        </Link>
      </div>
      <p className="mt-3">
        <Link
          href={`/${locale}/catalog`}
          className={`inline-flex items-center gap-0.5 text-sm text-navy/70 underline-offset-4 hover:text-brand hover:underline ${focusLight}`}
        >
          <BackLinkIcon className="h-4 w-4" />
          {text.backToCatalog}
        </Link>
      </p>
    </section>
  );
}
