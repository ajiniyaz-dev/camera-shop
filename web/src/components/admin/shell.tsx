"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { LanguageSwitcher } from "@/components/admin/language-switcher";
import { adminFetch } from "@/lib/admin-api";
import { translate, type Locale, type MessageKey } from "@/lib/i18n";

const LocaleContext = createContext<Locale>("ru");

export function useAdminLocale(): Locale {
  return useContext(LocaleContext);
}

const links: Array<{ href: string; key: MessageKey }> = [
  { href: "/admin", key: "dashboard" },
  { href: "/admin/products", key: "products" },
  { href: "/admin/brands", key: "brands" },
  { href: "/admin/categories", key: "categories" },
  { href: "/admin/imports", key: "imports" },
  { href: "/admin/profile", key: "profile" },
];

export function AdminShell({ locale, children }: { locale: Locale; children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [email, setEmail] = useState("");

  useEffect(() => {
    let cancelled = false;
    adminFetch("/api/auth/me")
      .then(async (response) => {
        if (!response.ok) {
          router.replace("/admin/login");
          return;
        }
        const body = (await response.json()) as { email?: string };
        if (!cancelled) {
          setEmail(body.email ?? "");
          setReady(true);
        }
      })
      .catch(() => router.replace("/admin/login"));
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function logout() {
    await adminFetch("/api/auth/logout", { method: "POST" });
    router.replace("/admin/login");
  }

  if (!ready) {
    return <p className="p-6 text-sm text-mute">{translate(locale, "loading")}</p>;
  }

  return (
    <LocaleContext.Provider value={locale}>
    <div className="min-h-screen bg-mist text-ink">
      <header className="sticky top-0 z-50 border-b border-line bg-navy text-white shadow-sm">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3">
          <p className="mr-2 text-sm font-semibold tracking-wide">{translate(locale, "appTitle")}</p>
          <nav className="flex flex-1 flex-wrap gap-1" aria-label={translate(locale, "appTitle")}>
            {links.map((link) => {
              const current = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={current ? "page" : undefined}
                  className={`rounded-lg px-2.5 py-1.5 text-sm transition-colors motion-reduce:transition-none ${
                    current ? "bg-brand text-white shadow-sm shadow-brand/40" : "text-white/80 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {translate(locale, link.key)}
                </Link>
              );
            })}
          </nav>
          <LanguageSwitcher locale={locale} tone="dark" />
          <span className="text-xs text-white/60">{email}</span>
          <button type="button" onClick={logout} className="rounded-lg border border-white/25 px-2.5 py-1.5 text-sm text-white/90 transition hover:bg-white/10">
            {translate(locale, "logout")}
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
    </LocaleContext.Provider>
  );
}
