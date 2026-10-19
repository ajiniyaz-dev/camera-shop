import { PriceMetaIcon } from "@/components/public/catalog-icons";
import { formatPublicPrice } from "@/lib/price-format";
import type { PublicPrice } from "@/lib/public-api";
import type { PublicLocale } from "@/lib/public-i18n";

export function PriceLabel({ price, locale }: { price: PublicPrice; locale: PublicLocale }) {
  const label = formatPublicPrice(price, locale);
  if (!label) return null;
  return (
    <p className="flex items-center gap-2 text-lg font-semibold leading-none text-ink">
      {price.status === "numeric" ? <PriceMetaIcon /> : null}
      <span>{label}</span>
    </p>
  );
}
