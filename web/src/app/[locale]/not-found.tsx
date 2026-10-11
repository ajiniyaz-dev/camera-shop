import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

import { messages, type PublicLocale } from "@/lib/public-i18n";

const lines: PublicLocale[] = ["ru", "uz", "en"];

export default function LocaleNotFound() {
  return (
    <main className="space-y-4 py-8">
      {lines.map((locale) => (
        <p key={locale} lang={locale}>
          <span className="text-2xl font-semibold">{messages[locale].notFound}</span>{" "}
          <Link href={`/${locale}`} className="underline underline-offset-4">
            {messages[locale].home}
          </Link>
        </p>
      ))}
    </main>
  );
}
