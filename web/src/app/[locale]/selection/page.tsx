import { redirect } from "next/navigation";

import { requireLocale } from "@/lib/public-api";
import { selectionNavHref } from "@/lib/selection";

/** Legacy inquiry-cart URL. Canonical path is `/{locale}/cart`. */
export default async function SelectionRedirectPage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = await requireLocale(params);
  redirect(selectionNavHref(locale));
}
