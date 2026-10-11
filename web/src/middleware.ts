import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const locale = request.nextUrl.pathname.split("/")[1] ?? "";
  const requestHeaders = new Headers(request.headers);
  if (locale === "ru" || locale === "uz" || locale === "en") {
    requestHeaders.set("x-catalog-locale", locale);
  }
  return NextResponse.next({ request: { headers: requestHeaders } });
}

export const config = {
  matcher: ["/((?!api|_next|media|admin).*)"],
};
