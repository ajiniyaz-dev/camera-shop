import Link from "next/link";

import { ProductPhoto } from "@/components/public/product-photo";
import { focusLight } from "@/components/public/brand-mark";
import type { PublicCard } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function HomeHero({
  companyName,
  locale,
  product,
}: {
  companyName: string;
  locale: PublicLocale;
  product: PublicCard | null;
}) {
  const text = messages[locale];
  return (
    <section className="relative isolate overflow-hidden rounded-2xl bg-gradient-to-br from-[#eaf1ff] via-[#edf3ff] to-[#f1f5f3] px-5 py-10 sm:px-9 sm:py-14 lg:min-h-[31rem] lg:px-12 lg:py-12" aria-labelledby="home-hero-title">
      <div className="grid min-h-full items-center gap-8 lg:grid-cols-[1fr_0.95fr] lg:gap-4">
        <div className="relative z-10 max-w-xl">
          <p className="mb-4 text-sm font-semibold tracking-wide text-brand">{companyName}</p>
          <h1 id="home-hero-title" className="text-3xl font-bold leading-[1.08] tracking-tight text-[#10131a] sm:text-4xl lg:text-[3.5rem]">
            {text.heroHeadline}
          </h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-[#394252] sm:text-lg sm:leading-8">{text.homeHeroBody}</p>
          <Link href={`/${locale}/catalog`} className={`mt-7 inline-flex min-h-12 items-center justify-center rounded-full bg-brand px-6 text-sm font-semibold text-white shadow-sm transition hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand ${focusLight}`}>
            {text.browseCatalog}
          </Link>
        </div>

        <div className="relative mx-auto flex h-64 w-full max-w-lg items-center justify-center sm:h-80 lg:h-[25rem]">
          <div aria-hidden="true" className="absolute right-[5%] top-[5%] h-[86%] w-[63%] rounded-[1.5rem] bg-gradient-to-br from-brand to-[#2268c5] shadow-lg shadow-brand/15" />
          <div aria-hidden="true" className="absolute bottom-[2%] right-[5%] h-[45%] w-[54%] rounded-tl-full bg-white/10" />
          {product?.image ? (
            <Link href={`/${locale}/products/${product.slug}`} aria-label={`${text.viewProduct}: ${product.name || product.model_display}`} className={`relative z-10 flex h-full w-full items-center justify-center ${focusLight}`}>
              <span className="flex h-[82%] w-[94%] items-center justify-center rounded-2xl bg-white/75 p-3 shadow-xl shadow-navy/10 sm:p-5">
                <ProductPhoto src={product.image.url} alt={product.image.alt || product.name || product.model_display} width={product.image.width} height={product.image.height} className="max-h-full max-w-full" />
              </span>
            </Link>
          ) : (
            <div aria-hidden="true" className="relative z-10 h-[75%] w-[75%] rounded-2xl bg-white/65" />
          )}
        </div>
      </div>
    </section>
  );
}
