import type { Metadata } from "next";
import Link from "next/link";

import { loadPublic, requireLocale, type CategoryNode } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";
import { pageMetadata, SITE_NAME } from "@/lib/seo";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const locale = await requireLocale(params);
  const text = messages[locale];
  return pageMetadata({
    locale,
    title: `${text.categories} | ${SITE_NAME}`,
    description: `${SITE_NAME}. ${text.categories}`,
    path: `/${locale}/categories`,
    index: true,
  });
}

export default async function CategoriesPage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = await requireLocale(params);
  const text = messages[locale];
  const body = await loadPublic<{ categories: CategoryNode[] }>(`/api/public/categories?locale=${locale}`);
  return (
    <main className="space-y-6">
      <h1 className="text-3xl font-semibold">{text.categories}</h1>
      {body.categories.length ? <CategoryTree nodes={body.categories} locale={locale} /> : <p>{text.noCategories}</p>}
    </main>
  );
}

function CategoryTree({
  nodes,
  locale,
  parent,
}: {
  nodes: CategoryNode[];
  locale: PublicLocale;
  parent?: string;
}) {
  const text = messages[locale];
  return (
    <ul className={parent ? "mt-3 space-y-3 border-l border-slate-200 pl-4" : "space-y-4"}>
      {nodes.map((node) => (
        <li key={node.slug}>
          <Link
            href={parent ? `/${locale}/categories/${parent}/${node.slug}` : `/${locale}/categories/${node.slug}`}
            className="font-medium underline underline-offset-4"
          >
            {node.name}
          </Link>
          <span className="ml-2 text-sm text-slate-600">
            {text.products}: {node.product_count}
          </span>
          {node.translation_fallback ? <p className="text-sm text-slate-600">{text.fallback}</p> : null}
          {node.description ? <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-700">{node.description}</p> : null}
          {node.children.length ? <CategoryTree nodes={node.children} locale={locale} parent={node.slug} /> : null}
        </li>
      ))}
    </ul>
  );
}
