import Link from "next/link";

import { focusLight } from "@/components/public/brand-mark";

export function Breadcrumbs({ label, items }: { label: string; items: Array<{ name: string; path: string }> }) {
  return (
    <nav aria-label={label}>
      <ol className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
        {items.map((item, index) => {
          const current = index === items.length - 1;
          return (
            <li key={`${item.path}-${index}`} className="flex min-w-0 items-center gap-2">
              {index > 0 ? (
                <span aria-hidden="true" className="text-teal">
                  /
                </span>
              ) : null}
              {current ? (
                <span className="truncate text-navy">{item.name}</span>
              ) : (
                <Link href={item.path} className={`text-brand underline-offset-4 hover:underline ${focusLight}`}>
                  {item.name}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
