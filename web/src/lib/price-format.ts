export type PublicPrice = {
  status: "numeric" | "on_request" | "hidden" | "unavailable" | string;
  amount: string | null;
  currency: string | null;
};

export type PriceLocale = "ru" | "uz" | "en";

const CURRENCY: Record<PriceLocale, string> = {
  ru: "сум",
  uz: "soʻm",
  en: "UZS",
};

const ON_REQUEST: Record<PriceLocale, string> = {
  ru: "По запросу",
  uz: "So'rov asosida",
  en: "On request",
};

const UNAVAILABLE: Record<PriceLocale, string> = {
  ru: "Цена недоступна",
  uz: "Narx mavjud emas",
  en: "Price unavailable",
};

/** Format a whole soʻm amount already returned by the public API. Do not convert again. */
export function formatUzsAmount(amount: string, locale: PriceLocale): string {
  const digits = amount.trim();
  if (!/^\d+$/.test(digits)) return digits;
  const grouped =
    locale === "en"
      ? digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",")
      : digits.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${grouped} ${CURRENCY[locale]}`;
}

export function formatPublicPrice(price: PublicPrice, locale: PriceLocale): string {
  if (price.status === "numeric" && price.amount && price.currency === "UZS") {
    return formatUzsAmount(price.amount, locale);
  }
  if (price.status === "on_request") {
    return ON_REQUEST[locale];
  }
  if (price.status === "unavailable") {
    return UNAVAILABLE[locale];
  }
  return "";
}

export type SelectionTotal = {
  total: string | null;
  excluded: boolean;
};

function addWhole(left: string, right: string): string {
  const a = left.split("").map(Number).reverse();
  const b = right.split("").map(Number).reverse();
  const out: number[] = [];
  let carry = 0;
  const length = Math.max(a.length, b.length);
  for (let index = 0; index < length; index += 1) {
    const sum = (a[index] ?? 0) + (b[index] ?? 0) + carry;
    out.push(sum % 10);
    carry = Math.floor(sum / 10);
  }
  if (carry) out.push(carry);
  return out.reverse().join("").replace(/^0+(?=\d)/, "") || "0";
}

/** Sum whole-soʻm amounts from public prices. Never applies a workbook formula. */
export function selectionTotal(prices: readonly PublicPrice[]): SelectionTotal {
  let sum = "0";
  let hasNumeric = false;
  let excluded = false;
  for (const price of prices) {
    if (price.status === "numeric" && price.currency === "UZS" && price.amount && /^\d+$/.test(price.amount)) {
      sum = addWhole(sum, price.amount);
      hasNumeric = true;
      continue;
    }
    if (price.status === "on_request" || price.status === "unavailable") {
      excluded = true;
    }
  }
  if (!hasNumeric) {
    return { total: null, excluded };
  }
  return { total: sum, excluded };
}
