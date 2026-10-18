"use client";

import { ShoppingCart } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { focusDark } from "@/components/public/brand-mark";
import { CATALOG_ICON_STROKE, SELECTION_CART_COLOR } from "@/components/public/catalog-icons";
import { messages, type PublicLocale } from "@/lib/public-i18n";
import {
  readSelection,
  SELECTION_EVENT,
  selectionBadgeCount,
  selectionNavHref,
  selectionNavLabel,
} from "@/lib/selection";

/**
 * Shared public navigation control for the browser-persisted product selection.
 * Used once in the site header (desktop and mobile). Not checkout.
 */
export function SelectionLink({ locale }: { locale: PublicLocale }) {
  const text = messages[locale];
  const [count, setCount] = useState(0);

  useEffect(() => {
    const sync = () => setCount(selectionBadgeCount(readSelection()));
    sync();
    window.addEventListener(SELECTION_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(SELECTION_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return (
    <Link
      href={selectionNavHref(locale)}
      aria-label={selectionNavLabel(text.selection, count)}
      className={`relative z-10 inline-flex min-h-11 min-w-11 items-center justify-center px-3 ${focusDark}`}
    >
      <span className="relative inline-flex h-6 w-6 shrink-0 items-center justify-center" aria-hidden="true">
        <ShoppingCart className="h-6 w-6" color={SELECTION_CART_COLOR} strokeWidth={CATALOG_ICON_STROKE} />
        <span
          className="pointer-events-none absolute -right-2.5 -top-2.5 flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px] font-semibold leading-none text-white ring-2 ring-navy"
          style={{ backgroundColor: SELECTION_CART_COLOR }}
        >
          {count}
        </span>
      </span>
    </Link>
  );
}

export { SELECTION_CART_COLOR };
