import { NextResponse } from "next/server";

import { normalizeLocale } from "@/lib/i18n";

export async function POST(request: Request) {
  const form = await request.formData();
  const locale = normalizeLocale(String(form.get("locale") ?? ""));
  const next = safeNext(String(form.get("next") ?? "/admin"));
  const response = NextResponse.redirect(new URL(next, request.url), 303);
  response.cookies.set("hikvision_ui_locale", locale, {
    path: "/",
    sameSite: "lax",
    httpOnly: false,
    maxAge: 60 * 60 * 24 * 365,
  });
  return response;
}

function safeNext(value: string): string {
  if (value.startsWith("/admin") && !value.startsWith("//")) {
    return value;
  }
  return "/admin";
}
