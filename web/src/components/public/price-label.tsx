import type { PublicPrice } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function PriceLabel({ price, locale }: { price: PublicPrice; locale: PublicLocale }) {
  const text = messages[locale];
  if (price.status === "numeric" && price.amount) {
    return <p className="text-lg font-semibold text-navy">${price.amount}</p>;
  }
  if (price.status === "on_request") {
    return <p className="text-lg font-semibold text-navy">{text.onRequest}</p>;
  }
  return null;
}
