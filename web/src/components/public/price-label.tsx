import { PriceMetaIcon } from "@/components/public/catalog-icons";
import { formatPublicPrice } from "@/lib/price-format";
import type { PublicPrice } from "@/lib/public-api";
import type { PublicLocale } from "@/lib/public-i18n";

export function PriceLabel({
  price,
  locale,
  compact = false,
  featured = false,
}: {
  price: PublicPrice;
  locale: PublicLocale;
  compact?: boolean;
  featured?: boolean;
}) {
  const label = formatPublicPrice(price, locale);
  if (!label) return null;
  const size = compact
    ? "text-base text-ink"
    : featured
      ? "text-[1.375rem] tracking-tight text-navy sm:text-2xl"
      : "text-lg text-ink";
  return (
    <p className={`flex items-center gap-2 font-semibold leading-none ${size}`}>
      {price.status === "numeric" && !compact && !featured ? <PriceMetaIcon /> : null}
      <span>{label}</span>
    </p>
  );
}
