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
    return <p className="p-6 text-sm text-neutral-600">{translate(locale, "loading")}</p>;
  }

  return (
    <LocaleContext.Provider value={locale}>
    <div className="min-h-screen bg-neutral-50 text-neutral-950">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3">
          <p className="mr-2 text-sm font-semibold">{translate(locale, "appTitle")}</p>
          <nav className="flex flex-1 flex-wrap gap-2" aria-label={translate(locale, "appTitle")}>
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={pathname === link.href ? "page" : undefined}
                className={`rounded px-2 py-1 text-sm ${pathname === link.href ? "bg-neutral-900 text-white" : "hover:bg-neutral-100"}`}
              >
                {translate(locale, link.key)}
              </Link>
            ))}
          </nav>
          <LanguageSwitcher locale={locale} />
          <span className="text-xs text-neutral-500">{email}</span>
          <button type="button" onClick={logout} className="rounded border border-neutral-300 px-2 py-1 text-sm">
            {translate(locale, "logout")}
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
    </LocaleContext.Provider>
  );
}
