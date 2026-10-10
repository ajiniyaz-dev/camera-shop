import { cookies } from "next/headers";

import { normalizeLocale, type Locale } from "@/lib/i18n";

export async function readLocale(): Promise<Locale> {
  const jar = await cookies();
  return normalizeLocale(jar.get("hikvision_ui_locale")?.value);
}
