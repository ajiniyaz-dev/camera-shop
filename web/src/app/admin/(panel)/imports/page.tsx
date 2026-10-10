"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminFetch, adminJson, errorMessage } from "@/lib/admin-api";
import { translate } from "@/lib/i18n";

type Job = { id: number; status: string; replace_prices: boolean; publish_new_products: boolean };

export default function ImportsPage() {
  const locale = useAdminLocale();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [message, setMessage] = useState("");
  const [replacePrices, setReplacePrices] = useState(false);
  const [publishNew, setPublishNew] = useState(true);
  const [hikvisionOverride, setHikvisionOverride] = useState("");
  const [ezvizOverride, setEzvizOverride] = useState("");

  function reload() {
    adminJson<{ jobs: Job[] }>("/api/admin/imports").then((body) => setJobs(body.jobs));
  }

  useEffect(reload, []);

  async function upload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    const form = new FormData(event.currentTarget);
    const data = new FormData();
    const hikvision = form.get("hikvision");
    const ezviz = form.get("ezviz");
    const overrides: string[] = [];
    if (hikvision instanceof File && hikvision.size > 0) {
      data.append("files", hikvision);
      overrides.push(hikvisionOverride);
    }
    if (ezviz instanceof File && ezviz.size > 0) {
      data.append("files", ezviz);
      overrides.push(ezvizOverride);
    }
    overrides.forEach((value) => data.append("source_overrides", value));
    data.append("replace_prices", replacePrices ? "true" : "false");
    data.append("publish_new_products", publishNew ? "true" : "false");
    const response = await adminFetch("/api/admin/imports", { method: "POST", body: data });
    if (!response.ok) {
      setMessage(await errorMessage(response));
      return;
    }
    const created = (await response.json()) as { id: number };
    window.location.assign(`/admin/imports/${created.id}`);
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">{translate(locale, "imports")}</h1>
      <form onSubmit={upload} className="mt-4 space-y-3 rounded border border-neutral-200 bg-white p-4">
        <h2 className="font-medium">{translate(locale, "uploadWorkbooks")}</h2>
        <label className="block text-sm">
          {translate(locale, "hikvisionFile")}
          <input name="hikvision" type="file" accept=".xlsx" className="mt-1 block" />
        </label>
        <label className="block text-sm">
          {translate(locale, "override")}
          <select value={hikvisionOverride} onChange={(event) => setHikvisionOverride(event.target.value)} className="mt-1 rounded border px-2 py-1">
            <option value="">{translate(locale, "auto")}</option>
            <option value="hikvision">Hikvision</option>
            <option value="ezviz">EZVIZ</option>
          </select>
        </label>
        <label className="block text-sm">
          {translate(locale, "ezvizFile")}
          <input name="ezviz" type="file" accept=".xlsx" className="mt-1 block" />
        </label>
        <label className="block text-sm">
          {translate(locale, "override")}
          <select value={ezvizOverride} onChange={(event) => setEzvizOverride(event.target.value)} className="mt-1 rounded border px-2 py-1">
            <option value="">{translate(locale, "auto")}</option>
            <option value="hikvision">Hikvision</option>
            <option value="ezviz">EZVIZ</option>
          </select>
        </label>
        <p className="text-sm text-neutral-600">{translate(locale, "sourceOverrideHint")}</p>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={replacePrices} onChange={(event) => setReplacePrices(event.target.checked)} />
          {translate(locale, "replacePrices")}
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={publishNew} onChange={(event) => setPublishNew(event.target.checked)} />
          {translate(locale, "publishNew")}
        </label>
        {message ? <p role="alert" className="text-sm text-red-700">{message}</p> : null}
        <button type="submit" className="rounded bg-neutral-900 px-4 py-2 text-sm text-white">
          {translate(locale, "preview")}
        </button>
      </form>
      {jobs.length === 0 ? <p className="mt-6 text-sm">{translate(locale, "noJobs")}</p> : null}
      <ul className="mt-4 divide-y rounded border border-neutral-200 bg-white">
        {jobs.map((job) => (
          <li key={job.id} className="flex items-center justify-between px-3 py-2 text-sm">
            <span>#{job.id}</span>
            <span>{job.status}</span>
            <Link href={`/admin/imports/${job.id}`} className="underline">
              {translate(locale, "details")}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
