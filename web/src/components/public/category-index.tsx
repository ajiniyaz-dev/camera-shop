import Link from "next/link";

import { focusLight } from "@/components/public/brand-mark";
import { CategoryOutlineIcon } from "@/components/public/catalog-icons";
import { showOriginalNote } from "@/lib/presentation";
import type { CategoryNode } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

/**
 * Balanced category directory. Parent cards stay compact; child series render as
 * chips instead of recursive nested trees that stretched uneven grid rows.
 */
export function CategoryIndex({ nodes, locale }: { nodes: CategoryNode[]; locale: PublicLocale }) {
  const text = messages[locale];
  return (
    <ul className="grid grid-cols-1 items-start gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {nodes.map((node) => (
        <li key={node.slug}>
          <article className="rounded-md border border-navy/10 bg-white p-4 shadow-sm transition-colors hover:border-brand hover:shadow-md">
            <Link
              href={`/${locale}/categories/${node.slug}`}
              className={`group flex items-start gap-3 ${focusLight}`}
            >
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-mist text-brand transition-colors group-hover:bg-navy group-hover:text-white">
                <CategoryOutlineIcon slug={node.slug} className="h-5 w-5" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="font-semibold leading-snug text-navy group-hover:text-brand">{node.name}</span>
                  <span
                    className="inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-mist px-1.5 text-[11px] font-medium tabular-nums text-navy/55"
                    title={`${node.product_count} ${text.products}`}
                  >
                    {node.product_count}
                  </span>
                </span>
                {showOriginalNote(node.translation_fallback, node.name) ? (
                  <span className="mt-1 block text-xs text-navy/60">{text.fallback}</span>
                ) : null}
              </span>
            </Link>
            {node.children.length ? (
              <ul className="mt-3 flex flex-wrap gap-1.5 border-t border-navy/10 pt-3">
                {node.children.map((child) => (
                  <li key={child.slug}>
                    <Link
                      href={`/${locale}/categories/${node.slug}/${child.slug}`}
                      className={`inline-flex max-w-full items-center rounded border border-navy/10 bg-mist px-2.5 py-1 text-xs font-medium text-navy/80 transition-colors hover:border-brand hover:bg-white hover:text-brand ${focusLight}`}
                    >
                      <span className="truncate">{child.name}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        </li>
      ))}
    </ul>
  );
}
