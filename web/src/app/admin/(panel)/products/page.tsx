"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminJson } from "@/lib/admin-api";
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
    adminJson<{ products: Row[]; total: number }>(`/api/admin/products?${params}`)
      .then((body) => {
        setRows(body.products);
        setTotal(body.total);
      })
      .catch(() => setMessage(translate(locale, "error")));
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
      {rows.length === 0 ? <p className="mt-6 text-sm">{translate(locale, "noProducts")}</p> : null}
      <ul className="mt-4 divide-y rounded border border-neutral-200 bg-white">
        {rows.map((row) => (
          <li key={row.id}>
            <Link href={`/admin/products/${row.id}`} className="flex flex-wrap items-center justify-between gap-2 px-3 py-3 text-sm hover:bg-neutral-50">
              <span className="font-medium">{row.model_display}</span>
              <span>{row.brand ?? translate(locale, "none")}</span>
              <span>{row.public_price_status === "numeric" ? `$${row.public_price_amount}` : row.public_price_status}</span>
              <span>{row.stock_status}</span>
              <span>{row.catalog_status}</span>
            </Link>
          </li>
        ))}
      </ul>
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
