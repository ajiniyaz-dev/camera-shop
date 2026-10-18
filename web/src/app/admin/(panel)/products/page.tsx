"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminJson } from "@/lib/admin-api";
import { listStatus } from "@/lib/admin-state";
import { translate } from "@/lib/i18n";

type Named = { id: number; name_ru: string | null };
type Row = {
  id: number;
  model_display: string;
  brand: string | null;
  catalog_status: string;
  stock_status: string;
  public_price_status: string;
  public_price_amount: string | null;
};

const productColumns =
  "grid grid-cols-[minmax(14rem,2.2fr)_minmax(7rem,1fr)_9rem_10rem_9rem] items-center gap-x-4 px-3";

function formatListPrice(row: Row): string {
  if (row.public_price_status !== "numeric" || !row.public_price_amount) {
    return row.public_price_status;
  }
  const amount = Number(row.public_price_amount);
  if (!Number.isFinite(amount)) return `$${row.public_price_amount}`;
  return `$${amount.toFixed(2)}`;
}

export default function ProductsPage() {
  const locale = useAdminLocale();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [stock, setStock] = useState("");
  const [sort, setSort] = useState("model");
  const [brandId, setBrandId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [brands, setBrands] = useState<Named[]>([]);
  const [categories, setCategories] = useState<Named[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    adminJson<{ brands: Named[] }>("/api/admin/brands").then((body) => setBrands(body.brands)).catch(() => setBrands([]));
    adminJson<{ categories: Named[] }>("/api/admin/categories").then((body) => setCategories(body.categories)).catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "20", sort });
    if (q.trim()) params.set("q", q.trim());
    if (status) params.set("catalog_status", status);
    if (stock) params.set("stock_status", stock);
    if (brandId) params.set("brand_id", brandId);
    if (categoryId) params.set("category_id", categoryId);
    setLoading(true);
    adminJson<{ products: Row[]; total: number }>(`/api/admin/products?${params}`)
      .then((body) => {
        setRows(body.products);
        setTotal(body.total);
        setFailed(false);
        setMessage("");
      })
      .catch(() => {
        setRows([]);
        setTotal(0);
        setFailed(true);
        setMessage(translate(locale, "error"));
      })
      .finally(() => setLoading(false));
  }, [locale, page, q, sort, status, stock, brandId, categoryId]);

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{translate(locale, "products")}</h1>
        <Link href="/admin/products/new" className="rounded bg-neutral-900 px-3 py-2 text-sm text-white">
          {translate(locale, "createProduct")}
        </Link>
      </div>
      <form className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" onSubmit={(event) => event.preventDefault()}>
        <label className="text-sm">
          {translate(locale, "search")}
          <input value={q} onChange={(event) => { setPage(1); setQ(event.target.value); }} className="mt-1 w-full rounded border border-neutral-300 px-3 py-2" />
        </label>
        <label className="text-sm">
          {translate(locale, "status")}
          <select value={status} onChange={(event) => { setPage(1); setStatus(event.target.value); }} className="mt-1 w-full rounded border border-neutral-300 px-3 py-2">
            <option value="">{translate(locale, "all")}</option>
            <option value="published">{translate(locale, "published")}</option>
            <option value="draft">{translate(locale, "draft")}</option>
            <option value="archived">{translate(locale, "archived")}</option>
          </select>
        </label>
        <label className="text-sm">
          {translate(locale, "stock")}
          <select value={stock} onChange={(event) => { setPage(1); setStock(event.target.value); }} className="mt-1 w-full rounded border border-neutral-300 px-3 py-2">
            <option value="">{translate(locale, "all")}</option>
            <option value="in_stock">{translate(locale, "inStock")}</option>
            <option value="out_of_stock">{translate(locale, "outOfStock")}</option>
          </select>
        </label>
        <label className="text-sm">
          {translate(locale, "sort")}
          <select value={sort} onChange={(event) => setSort(event.target.value)} className="mt-1 w-full rounded border border-neutral-300 px-3 py-2">
            <option value="model">{translate(locale, "model")}</option>
            <option value="updated">{translate(locale, "saved")}</option>
            <option value="price">{translate(locale, "price")}</option>
          </select>
        </label>
        <label className="text-sm">
          {translate(locale, "brand")}
          <select value={brandId} onChange={(event) => { setPage(1); setBrandId(event.target.value); }} className="mt-1 w-full rounded border border-neutral-300 px-3 py-2">
            <option value="">{translate(locale, "all")}</option>
            {brands.map((brand) => (
              <option key={brand.id} value={brand.id}>{brand.name_ru}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          {translate(locale, "category")}
          <select value={categoryId} onChange={(event) => { setPage(1); setCategoryId(event.target.value); }} className="mt-1 w-full rounded border border-neutral-300 px-3 py-2">
            <option value="">{translate(locale, "all")}</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name_ru}</option>
            ))}
          </select>
        </label>
      </form>
      {message ? <p role="alert" className="mt-3 text-sm text-red-700">{message}</p> : null}
      {listStatus(loading, failed, rows.length) === "loading" ? <p className="mt-6 text-sm">{translate(locale, "loading")}</p> : null}
      {listStatus(loading, failed, rows.length) === "empty" ? <p className="mt-6 text-sm">{translate(locale, "noProducts")}</p> : null}
      {rows.length > 0 ? (
        <div className="mt-4 overflow-x-auto rounded border border-neutral-200 bg-white">
          <div className="min-w-[46rem]" role="table">
            <div role="row" className={`${productColumns} border-b border-neutral-200 py-2 text-xs font-medium text-neutral-500`}>
              <span role="columnheader" className="text-left">{translate(locale, "model")}</span>
              <span role="columnheader" className="text-left">{translate(locale, "brand")}</span>
              <span role="columnheader" className="text-left">{translate(locale, "price")}</span>
              <span role="columnheader" className="text-left">{translate(locale, "stock")}</span>
              <span role="columnheader" className="text-left">{translate(locale, "status")}</span>
            </div>
            <div role="rowgroup" className="divide-y divide-neutral-100">
              {rows.map((row) => {
                const brand = row.brand ?? translate(locale, "none");
                return (
                  <Link
                    key={row.id}
                    href={`/admin/products/${row.id}`}
                    role="row"
                    className={`${productColumns} py-3 text-sm hover:bg-neutral-50`}
                  >
                    <span role="cell" className="min-w-0 truncate text-left font-medium" title={row.model_display}>
                      {row.model_display}
                    </span>
                    <span role="cell" className="min-w-0 truncate text-left" title={brand}>
                      {brand}
                    </span>
                    <span role="cell" className="whitespace-nowrap text-left tabular-nums">
                      {formatListPrice(row)}
                    </span>
                    <span role="cell" className="whitespace-nowrap text-left">{row.stock_status}</span>
                    <span role="cell" className="whitespace-nowrap text-left">{row.catalog_status}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      ) : null}
      <div className="mt-4 flex items-center gap-3 text-sm">
        <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded border px-3 py-1 disabled:opacity-40">
          {translate(locale, "previous")}
        </button>
        <span>
          {translate(locale, "page")} {page} / {Math.max(1, Math.ceil(total / 20))}
        </span>
        <button type="button" disabled={page * 20 >= total} onClick={() => setPage(page + 1)} className="rounded border px-3 py-1 disabled:opacity-40">
          {translate(locale, "next")}
        </button>
      </div>
    </section>
  );
}
