"use client";

import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminJson, ApiError } from "@/lib/admin-api";
import { translate } from "@/lib/i18n";

type Category = {
  id: number;
  parent_id: number | null;
  name_ru: string | null;
  name_uz: string | null;
  name_en: string | null;
  is_published: boolean;
};

const field = "mt-1 w-full rounded border border-neutral-300 px-3 py-2";

export default function CategoriesPage() {
  const locale = useAdminLocale();
  const [rows, setRows] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [message, setMessage] = useState("");

  function reload() {
    adminJson<{ categories: Category[] }>("/api/admin/categories").then((body) => setRows(body.categories));
  }

  useEffect(reload, []);

  async function create(event: React.FormEvent) {
    event.preventDefault();
    try {
      await adminJson("/api/admin/categories", { method: "POST" }, {
        name_ru: name,
        parent_id: parentId ? Number(parentId) : null,
        is_published: true,
      });
      setName("");
      reload();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  async function save(row: Category) {
    try {
      await adminJson(`/api/admin/categories/${row.id}`, { method: "PATCH" }, {
        name_ru: row.name_ru,
        name_uz: row.name_uz,
        name_en: row.name_en,
        parent_id: row.parent_id,
        is_published: row.is_published,
      });
      setMessage(translate(locale, "saved"));
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">{translate(locale, "categories")}</h1>
      <form onSubmit={create} className="mt-4 flex flex-wrap items-end gap-2">
        <label className="text-sm">
          {translate(locale, "name")} RU
          <input required value={name} onChange={(event) => setName(event.target.value)} className={field} />
        </label>
        <label className="text-sm">
          {translate(locale, "category")}
          <select value={parentId} onChange={(event) => setParentId(event.target.value)} className={field}>
            <option value="">{translate(locale, "none")}</option>
            {rows.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name_ru}
              </option>
            ))}
          </select>
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
              <input aria-label="RU" value={row.name_ru ?? ""} onChange={(event) => setRows(edit(rows, row.id, { name_ru: event.target.value }))} className={field} />
              <input aria-label="UZ" value={row.name_uz ?? ""} onChange={(event) => setRows(edit(rows, row.id, { name_uz: event.target.value }))} className={field} />
              <input aria-label="EN" value={row.name_en ?? ""} onChange={(event) => setRows(edit(rows, row.id, { name_en: event.target.value }))} className={field} />
            </div>
            <label className="mt-2 block text-sm">
              {translate(locale, "parentCategory")}
              <select value={row.parent_id ?? ""} onChange={(event) => setRows(edit(rows, row.id, { parent_id: event.target.value ? Number(event.target.value) : null }))} className={field}>
                <option value="">{translate(locale, "none")}</option>
                {rows.filter((item) => item.id !== row.id).map((item) => (
                  <option key={item.id} value={item.id}>{item.name_ru}</option>
                ))}
              </select>
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

function edit(rows: Category[], id: number, patch: Partial<Category>): Category[] {
  return rows.map((row) => (row.id === id ? { ...row, ...patch } : row));
}
