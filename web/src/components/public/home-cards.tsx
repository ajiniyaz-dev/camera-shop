import Link from "next/link";

import { CameraGlyph, focusLight } from "@/components/public/brand-mark";
import { ProductPhoto } from "@/components/public/product-photo";
import { CategoryGlyph } from "@/components/public/home-category-card";
import { billingPeriod, isServicePlan, showOriginalNote } from "@/lib/presentation";
import { categoryPath, type CategoryNode, type PublicCard } from "@/lib/public-api";
import { formatPublicPrice } from "@/lib/price-format";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function HomeCategoryCard({
  category,
  locale,
}: {
  category: CategoryNode;
  locale: PublicLocale;
}) {
  const text = messages[locale];
  return (
    <Link
      href={categoryPath(locale, category.slug, null)}
      className={`group flex h-full min-h-24 items-center gap-3 rounded-xl border border-line bg-white p-4 shadow-card outline-none transition duration-200 hover:border-sky/70 hover:shadow-lift motion-reduce:transition-none ${focusLight}`}
    >
      <span className="grid h-12 w-12 shrink-0 place-items-center rounded-lg bg-mist text-brand transition-colors group-hover:bg-brand group-hover:text-white motion-reduce:transition-none">
        <CategoryGlyph slug={category.slug} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-base font-semibold leading-snug text-ink group-hover:text-brand">
          {category.name}
        </span>
        {showOriginalNote(category.translation_fallback, category.name) ? (
          <span className="mt-1 block text-xs text-mute">{text.fallback}</span>
        ) : null}
      </span>
    </Link>
  );
}

export function HomeHeroProduct({ product, locale }: { product: PublicCard; locale: PublicLocale }) {
  const text = messages[locale];
  const meta = [product.brand?.name, product.category?.name].filter(Boolean).join(" · ");
  return (
    <Link
      href={`/${locale}/products/${product.slug}`}
      className={`group flex h-full flex-col rounded-xl bg-white p-4 text-ink shadow-card outline-none ring-1 ring-white/20 transition duration-200 hover:ring-2 hover:ring-sky motion-reduce:transition-none ${focusLight}`}
    >
      {product.image ? (
        <span className="flex h-48 w-full items-center justify-center sm:h-56">
          <ProductPhoto src={product.image.url} alt={product.image.alt} width={product.image.width} height={product.image.height} />
        </span>
      ) : null}
      {isServicePlan(product) ? <span className="mt-3 block text-xs font-semibold uppercase tracking-[0.14em] text-teal">{text.service}</span> : null}
      <span className={`${isServicePlan(product) ? "mt-1" : "mt-3"} line-clamp-2 text-lg font-semibold leading-snug group-hover:text-brand`}>
        {product.name || product.model_display}
      </span>
      <span className="mt-1 truncate text-sm text-mute">
        {text.model}: {product.model_display}
        {billingLabel(product.option_label, text)}
      </span>
      {labeledMeta(product, text) || meta ? <span className="mt-1 truncate text-sm text-mute">{labeledMeta(product, text) || meta}</span> : null}
      <span className="mt-3 text-xl font-semibold text-ink">{formatPublicPrice(product.price, locale)}</span>
      <span className="mt-3 text-sm font-medium text-brand">{text.viewProduct}</span>
    </Link>
  );
}

export function HomeProductCard({ product, locale }: { product: PublicCard; locale: PublicLocale }) {
  const text = messages[locale];
  const meta = [product.brand?.name, product.category?.name].filter(Boolean).join(" · ");
  return (
    <article className="h-full">
      <Link
        href={`/${locale}/products/${product.slug}`}
        className={`group flex h-full flex-col overflow-hidden rounded-xl border border-[#E5E7EB] bg-white shadow-sm outline-none transition duration-200 hover:border-[#2563EB] hover:shadow-md motion-reduce:transition-none ${focusLight}`}
      >
        <span className="flex flex-1 flex-col gap-1 p-5 sm:p-6">
          {isServicePlan(product) ? <span className="text-xs font-semibold uppercase tracking-[0.14em] text-[#2563EB]">{text.service}</span> : null}
          <h3 className="line-clamp-2 text-base font-semibold leading-snug text-[#1D4ED8] group-hover:text-[#2563EB]">
            {product.name || product.model_display}
          </h3>
          <span className="truncate text-sm text-mute">
            {text.model}: {product.model_display}
            {billingLabel(product.option_label, text) || (product.option_label ? ` · ${product.option_label}` : "")}
          </span>
          <span className="min-h-5 truncate text-sm text-mute">{labeledMeta(product, text) || meta}</span>
          <span className="mt-3 border-t border-[#E5E7EB] pt-3 text-xl font-semibold text-[#1D4ED8]">
            {formatPublicPrice(product.price, locale)}
          </span>
          <span className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-brand">
            {text.viewProduct}<span aria-hidden="true">→</span>
          </span>
        </span>
        {product.image ? (
          <span className="flex h-44 w-full items-center justify-center px-5 pb-5 sm:h-52 sm:px-7 sm:pb-6">
            <ProductPhoto src={product.image.url} alt={product.image.alt} width={product.image.width} height={product.image.height} />
          </span>
        ) : (
          <span className="flex h-40 flex-col items-center justify-center gap-2 px-4 pb-5 text-center text-sm text-mute">
            <CameraGlyph className="h-9 w-9 text-[#1D4ED8]" />
            {text.noImage}
          </span>
        )}
      </Link>
    </article>
  );
}

function billingLabel(
  option: string | null,
  text: { billing: string; billingMonthly: string; billingYearly: string },
): string {
  const period = billingPeriod(option);
  if (period === "monthly") return ` · ${text.billing}: ${text.billingMonthly}`;
  if (period === "yearly") return ` · ${text.billing}: ${text.billingYearly}`;
  return "";
}

function labeledMeta(
  product: PublicCard,
  text: { brand: string; category: string },
): string {
  const brand = product.brand?.name;
  const category = product.category?.name;
  if (brand && category && brand === category) {
    return `${text.brand}: ${brand} · ${text.category}: ${category}`;
  }
  return "";
}
