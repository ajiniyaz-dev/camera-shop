"use client";

import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminJson, ApiError } from "@/lib/admin-api";
import { translate } from "@/lib/i18n";

type Brand = {
  id: number;
  name_ru: string | null;
  name_uz: string | null;
  name_en: string | null;
  description_ru: string | null;
  is_published: boolean;
};

const field = "mt-1 w-full rounded border border-neutral-300 px-3 py-2";

export default function BrandsPage() {
  const locale = useAdminLocale();
  const [rows, setRows] = useState<Brand[]>([]);
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");

  function reload() {
    adminJson<{ brands: Brand[] }>("/api/admin/brands").then((body) => setRows(body.brands));
  }

  useEffect(reload, []);

  async function create(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await adminJson("/api/admin/brands", { method: "POST" }, { name_ru: name, is_published: true });
      setName("");
      reload();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  async function save(row: Brand) {
    setMessage("");
    try {
      await adminJson(`/api/admin/brands/${row.id}`, { method: "PATCH" }, row);
      setMessage(translate(locale, "saved"));
      reload();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">{translate(locale, "brands")}</h1>
      <form onSubmit={create} className="mt-4 flex flex-wrap items-end gap-2">
        <label className="text-sm">
          {translate(locale, "name")} RU
          <input required value={name} onChange={(event) => setName(event.target.value)} className={field} />
        </label>
        <button type="submit" className="rounded bg-neutral-900 px-3 py-2 text-sm text-white">
          {translate(locale, "save")}
        </button>
      </form>
      {message ? <p className="mt-3 text-sm">{message}</p> : null}
      {rows.length === 0 ? <p className="mt-6 text-sm">{translate(locale, "empty")}</p> : null}
      <ul className="mt-4 space-y-3">
        {rows.map((row) => (
          <li key={row.id} className="rounded border border-neutral-200 bg-white p-3">
            <div className="grid gap-2 sm:grid-cols-3">
              <input aria-label="RU" value={row.name_ru ?? ""} onChange={(event) => setRows(update(rows, row.id, { name_ru: event.target.value }))} className={field} />
              <input aria-label="UZ" value={row.name_uz ?? ""} onChange={(event) => setRows(update(rows, row.id, { name_uz: event.target.value }))} className={field} />
              <input aria-label="EN" value={row.name_en ?? ""} onChange={(event) => setRows(update(rows, row.id, { name_en: event.target.value }))} className={field} />
            </div>
            <label className="mt-2 block text-sm">
              {translate(locale, "description")}
              <textarea aria-label={translate(locale, "description")} value={row.description_ru ?? ""} onChange={(event) => setRows(update(rows, row.id, { description_ru: event.target.value }))} className={field} rows={2} />
            </label>
            <label className="mt-2 flex items-center gap-2 text-sm">
              <input type="checkbox" checked={row.is_published} onChange={(event) => setRows(update(rows, row.id, { is_published: event.target.checked }))} />
              {translate(locale, "published")}
            </label>
            <button type="button" onClick={() => save(row)} className="mt-2 text-sm underline">
              {translate(locale, "save")}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function update(rows: Brand[], id: number, patch: Partial<Brand>): Brand[] {
  return rows.map((row) => (row.id === id ? { ...row, ...patch } : row));
}
