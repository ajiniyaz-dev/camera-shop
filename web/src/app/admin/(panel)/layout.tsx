import type { ReactNode } from "react";

import { AdminShell } from "@/components/admin/shell";
import { readLocale } from "@/lib/locale";

export const dynamic = "force-dynamic";

export default async function PanelLayout({ children }: { children: ReactNode }) {
  const locale = await readLocale();
  return <AdminShell locale={locale}>{children}</AdminShell>;
}
