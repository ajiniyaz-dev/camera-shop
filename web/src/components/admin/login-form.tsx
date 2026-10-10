"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { LanguageSwitcher } from "@/components/admin/language-switcher";
import { adminJson, ApiError } from "@/lib/admin-api";
import { translate, type Locale } from "@/lib/i18n";

export function LoginForm({ locale }: { locale: Locale }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setMessage("");
    try {
      await adminJson("/api/auth/login", { method: "POST" }, { email, password });
      router.replace("/admin");
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <div className="mb-6 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{translate(locale, "login")}</h1>
        <LanguageSwitcher locale={locale} />
      </div>
      <form onSubmit={submit} className="space-y-4 rounded border border-neutral-200 bg-white p-4">
        <label className="block text-sm">
          {translate(locale, "email")}
          <input
            type="email"
            name="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          {translate(locale, "password")}
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
          />
        </label>
        {message ? (
          <p role="alert" className="text-sm text-red-700">
            {message}
          </p>
        ) : null}
        <button type="submit" disabled={pending} className="rounded bg-neutral-900 px-4 py-2 text-sm text-white">
          {translate(locale, "signIn")}
        </button>
      </form>
    </main>
  );
}
