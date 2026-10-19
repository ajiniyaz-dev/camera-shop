"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminJson } from "@/lib/admin-api";
import { translate } from "@/lib/i18n";

type Dashboard = {
  products: { total: number; published: number; draft: number; archived: number };
  brands: number;
  categories: number;
  review: { pending_conflicts: number; invalid_files: number };
  recent_imports: Array<{ id: number; status: string }>;
};

export default function DashboardPage() {
  const locale = useAdminLocale();
  const [data, setData] = useState<Dashboard | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    adminJson<Dashboard>("/api/admin/dashboard")
      .then(setData)
      .catch(() => setMessage(translate(locale, "error")));
  }, [locale]);

  if (!data) {
    return <p>{message || translate(locale, "loading")}</p>;
  }

  const cards = [
    [translate(locale, "total"), data.products.total],
    [translate(locale, "published"), data.products.published],
    [translate(locale, "draft"), data.products.draft],
    [translate(locale, "archived"), data.products.archived],
    [translate(locale, "brandsCount"), data.brands],
    [translate(locale, "categoriesCount"), data.categories],
    [translate(locale, "conflicts"), data.review.pending_conflicts],
    [translate(locale, "invalidFiles"), data.review.invalid_files],
  ] as const;

  return (
    <section>
      <h1 className="text-2xl font-semibold text-ink">{translate(locale, "dashboard")}</h1>
      {message ? (
        <p role="alert" className="mt-3 text-sm text-red-700">
          {message}
        </p>
      ) : null}
      <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([label, value]) => (
          <li key={label} className="surface-card p-4">
            <p className="text-sm text-mute">{label}</p>
            <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
            <span aria-hidden="true" className="mt-3 block h-1 w-8 rounded-full bg-sky/80" />
          </li>
        ))}
      </ul>
      <h2 className="mt-8 text-lg font-semibold text-ink">{translate(locale, "recentImports")}</h2>
      {data.recent_imports.length === 0 ? (
        <p className="mt-2 text-sm text-mute">{translate(locale, "noJobs")}</p>
      ) : (
        <ul className="mt-2 divide-y divide-line overflow-hidden rounded-xl border border-line bg-white shadow-sm">
          {data.recent_imports.map((job) => (
            <li key={job.id} className="flex items-center justify-between gap-3 px-3 py-2.5 text-sm">
              <span className="font-medium text-ink">#{job.id}</span>
              <span className="rounded-full bg-mist px-2 py-0.5 text-xs font-medium text-mute">{job.status}</span>
              <Link href={`/admin/imports/${job.id}`} className="font-medium text-brand underline-offset-4 hover:underline">
                {translate(locale, "details")}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
