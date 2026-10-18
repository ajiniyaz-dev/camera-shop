import type { Metadata } from "next";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { PageHeading } from "@/components/public/page-heading";
import { SelectionView } from "@/components/public/selection-view";
import { requireLocale } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
import { selectionNavHref } from "@/lib/selection";
import { pageMetadata, SITE_NAME } from "@/lib/seo";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const locale = await requireLocale(params);
  const text = messages[locale];
  return pageMetadata({
    locale,
    title: `${text.selection} | ${SITE_NAME}`,
    description: text.selectionNote,
    path: selectionNavHref(locale),
    index: false,
  });
}

export default async function CartPage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = await requireLocale(params);
  const text = messages[locale];
  const cartPath = selectionNavHref(locale);
  return (
    <main className="space-y-8">
      <Breadcrumbs
        label={text.navigation}
        items={[
          { name: text.home, path: `/${locale}` },
          { name: text.selection, path: cartPath },
        ]}
      />
      <PageHeading title={text.selection} />
      <SelectionView locale={locale} />
    </main>
  );
}
