"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminFetch, adminJson, ApiError, errorMessage } from "@/lib/admin-api";
import { translate } from "@/lib/i18n";

type Named = { id: number; name_ru: string | null };
type Spec = {
  sort_order: number;
  name_ru: string;
  value_ru: string;
  name_uz: string;
  value_uz: string;
  name_en: string;
  value_en: string;
};
type ImageRow = { id: number; url: string; is_primary: boolean; alt_text: string | null };
type Product = {
  id: number;
  model_display: string;
  option_label: string | null;
  brand_id: number | null;
  category_id: number | null;
  product_kind: "product" | "service";
  stock_status: "in_stock" | "out_of_stock";
  catalog_status: "draft" | "published" | "archived";
  public_price_status: "numeric" | "on_request" | "hidden";
  public_price_amount: string | null;
  price_locked: boolean;
  model_locked: boolean;
  translations: Record<string, { localized_name: string | null; description: string | null; description_locked: boolean }>;
  specifications: Array<{
    sort_order: number;
    translations: Record<string, { name: string; value: string }>;
  }>;
  images: ImageRow[];
  source: {
    source_code: string;
    source_worksheet: string;
    source_row: number;
    source_price_kind: string;
    source_price_amount: string | null;
    internal_note: string | null;
  } | null;
};

const field = "mt-1 w-full rounded border border-neutral-300 px-3 py-2";

export function ProductEditor({ productId }: { productId?: number }) {
  const locale = useAdminLocale();
  const router = useRouter();
  const [brands, setBrands] = useState<Named[]>([]);
  const [categories, setCategories] = useState<Named[]>([]);
  const [model, setModel] = useState("");
  const [option, setOption] = useState("");
  const [brandId, setBrandId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [kind, setKind] = useState<"product" | "service">("product");
  const [stock, setStock] = useState<"in_stock" | "out_of_stock">("in_stock");
  const [status, setStatus] = useState<"draft" | "published" | "archived">("draft");
  const [priceStatus, setPriceStatus] = useState<"numeric" | "on_request" | "hidden">("on_request");
  const [amount, setAmount] = useState("");
  const [names, setNames] = useState({ ru: "", uz: "", en: "" });
  const [descriptions, setDescriptions] = useState({ ru: "", uz: "", en: "" });
  const [specs, setSpecs] = useState<Spec[]>([]);
  const [images, setImages] = useState<ImageRow[]>([]);
  const [source, setSource] = useState<Product["source"]>(null);
  const [locks, setLocks] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [saved, setSaved] = useState(false);
  const [alt, setAlt] = useState("");

  useEffect(() => {
    adminJson<{ brands: Named[] }>("/api/admin/brands").then((body) => setBrands(body.brands));
    adminJson<{ categories: Named[] }>("/api/admin/categories").then((body) => setCategories(body.categories));
    if (productId === undefined) {
      return;
    }
    adminJson<Product>(`/api/admin/products/${productId}`).then((product) => {
      setModel(product.model_display);
      setOption(product.option_label ?? "");
      setBrandId(product.brand_id ? String(product.brand_id) : "");
      setCategoryId(product.category_id ? String(product.category_id) : "");
      setKind(product.product_kind);
      setStock(product.stock_status);
      setStatus(product.catalog_status);
      setPriceStatus(product.public_price_status);
      setAmount(product.public_price_amount ?? "");
      setNames({
        ru: product.translations.ru?.localized_name ?? "",
        uz: product.translations.uz?.localized_name ?? "",
        en: product.translations.en?.localized_name ?? "",
      });
      setDescriptions({
        ru: product.translations.ru?.description ?? "",
        uz: product.translations.uz?.description ?? "",
        en: product.translations.en?.description ?? "",
      });
      setSpecs(
        product.specifications.map((spec) => ({
          sort_order: spec.sort_order,
          name_ru: spec.translations.ru?.name ?? "",
          value_ru: spec.translations.ru?.value ?? "",
          name_uz: spec.translations.uz?.name ?? "",
          value_uz: spec.translations.uz?.value ?? "",
          name_en: spec.translations.en?.name ?? "",
          value_en: spec.translations.en?.value ?? "",
        })),
      );
      setImages(product.images);
      setSource(product.source);
      const nextLocks = [
        product.model_locked ? "model" : "",
        product.price_locked ? "price" : "",
        product.translations.ru?.description_locked ? "description" : "",
      ].filter(Boolean);
      setLocks(nextLocks);
    });
  }, [productId]);

  function payload() {
    return {
      model_display: model,
      option_label: option || null,
      brand_id: brandId ? Number(brandId) : null,
      category_id: categoryId ? Number(categoryId) : null,
      product_kind: kind,
      stock_status: stock,
      catalog_status: status,
      price: { status: priceStatus, amount: priceStatus === "on_request" ? null : amount || null },
      translations: {
        ru: { localized_name: names.ru || null, description: descriptions.ru || null },
        uz: { localized_name: names.uz || null, description: descriptions.uz || null },
        en: { localized_name: names.en || null, description: descriptions.en || null },
      },
      specifications: specs,
    };
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setSaved(false);
    setMessage("");
    try {
      const path = productId === undefined ? "/api/admin/products" : `/api/admin/products/${productId}`;
      const method = productId === undefined ? "POST" : "PATCH";
      const savedProduct = await adminJson<Product>(path, { method }, payload());
      setSaved(true);
      if (productId === undefined) {
        router.replace(`/admin/products/${savedProduct.id}`);
      }
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  async function archive() {
    if (productId === undefined || !window.confirm(translate(locale, "archiveConfirm"))) {
      return;
    }
    try {
      await adminJson(`/api/admin/products/${productId}/archive`, { method: "POST" }, { confirm: true });
      setStatus("archived");
      setSaved(true);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  async function uploadImage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (productId === undefined) {
      return;
    }
    const data = new FormData(event.currentTarget);
    const response = await adminFetch(`/api/admin/products/${productId}/images`, { method: "POST", body: data });
    if (!response.ok) {
      setMessage(await errorMessage(response));
      return;
    }
    const image = (await response.json()) as ImageRow;
    setImages((current) => [...current, image]);
    event.currentTarget.reset();
  }

  async function makePrimary(imageId: number) {
    if (productId === undefined) {
      return;
    }
    await adminJson(`/api/admin/products/${productId}/images/${imageId}`, { method: "PATCH" }, { is_primary: true });
    setImages((current) => current.map((image) => ({ ...image, is_primary: image.id === imageId })));
  }

  async function removeImage(imageId: number) {
    if (productId === undefined || !window.confirm(translate(locale, "removeImage"))) {
      return;
    }
    const response = await adminFetch(`/api/admin/products/${productId}/images/${imageId}`, { method: "DELETE" });
    if (!response.ok) {
      setMessage(await errorMessage(response));
      return;
    }
    setImages((current) => current.filter((image) => image.id !== imageId));
  }

  return (
    <section>
      <p className="text-sm">
        <Link href="/admin/products" className="underline">
          {translate(locale, "back")}
        </Link>
      </p>
      <h1 className="mt-2 text-2xl font-semibold">
        {productId === undefined ? translate(locale, "createProduct") : translate(locale, "editProduct")}
      </h1>
      {locks.length > 0 ? <p className="mt-2 text-sm text-neutral-600">{translate(locale, "locked")}</p> : null}
      <form onSubmit={save} className="mt-4 space-y-4">
        <label className="block text-sm">
          {translate(locale, "model")}
          <input required value={model} onChange={(event) => setModel(event.target.value)} className={field} />
        </label>
        <label className="block text-sm">
          {translate(locale, "option")}
          <input value={option} onChange={(event) => setOption(event.target.value)} className={field} />
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm">
            {translate(locale, "brand")}
            <select value={brandId} onChange={(event) => setBrandId(event.target.value)} className={field}>
              <option value="">{translate(locale, "none")}</option>
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name_ru}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            {translate(locale, "category")}
            <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)} className={field}>
              <option value="">{translate(locale, "none")}</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name_ru}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="block text-sm">
            {translate(locale, "kind")}
            <select value={kind} onChange={(event) => setKind(event.target.value as "product" | "service")} className={field}>
              <option value="product">{translate(locale, "productKind")}</option>
              <option value="service">{translate(locale, "service")}</option>
            </select>
          </label>
          <label className="block text-sm">
            {translate(locale, "stock")}
            <select value={stock} onChange={(event) => setStock(event.target.value as "in_stock" | "out_of_stock")} className={field}>
              <option value="in_stock">{translate(locale, "inStock")}</option>
              <option value="out_of_stock">{translate(locale, "outOfStock")}</option>
            </select>
          </label>
          <label className="block text-sm">
            {translate(locale, "status")}
            <select value={status} onChange={(event) => setStatus(event.target.value as "draft" | "published" | "archived")} className={field}>
              <option value="draft">{translate(locale, "draft")}</option>
              <option value="published">{translate(locale, "published")}</option>
              <option value="archived">{translate(locale, "archived")}</option>
            </select>
          </label>
        </div>
        <fieldset className="rounded border border-neutral-200 p-3">
          <legend className="px-1 text-sm font-medium">{translate(locale, "price")}</legend>
          <p className="text-sm text-neutral-600">{translate(locale, "noDiscount")}</p>
          <p className="text-sm text-neutral-600">{translate(locale, "blankPrice")}</p>
          <p className="text-sm text-neutral-600">{translate(locale, "stockIndependent")}</p>
          <div className="mt-2 grid gap-3 sm:grid-cols-2">
            <label className="block text-sm">
              {translate(locale, "status")}
              <select value={priceStatus} onChange={(event) => setPriceStatus(event.target.value as "numeric" | "on_request" | "hidden")} className={field}>
                <option value="numeric">{translate(locale, "numeric")}</option>
                <option value="on_request">{translate(locale, "onRequest")}</option>
                <option value="hidden">{translate(locale, "hidden")}</option>
              </select>
            </label>
            <label className="block text-sm">
              {translate(locale, "amount")}
              <input
                inputMode="decimal"
                value={priceStatus === "on_request" ? "" : amount}
                disabled={priceStatus === "on_request"}
                onChange={(event) => setAmount(event.target.value)}
                className={field}
              />
            </label>
          </div>
        </fieldset>
        {(["ru", "uz", "en"] as const).map((code) => (
          <fieldset key={code} className="rounded border border-neutral-200 p-3">
            <legend className="px-1 text-sm font-medium">{code.toUpperCase()}</legend>
            <label className="block text-sm">
              {translate(locale, "name")}
              <input value={names[code]} onChange={(event) => setNames({ ...names, [code]: event.target.value })} className={field} />
            </label>
            <label className="mt-2 block text-sm">
              {translate(locale, "description")}
              <textarea value={descriptions[code]} onChange={(event) => setDescriptions({ ...descriptions, [code]: event.target.value })} className={field} rows={3} />
            </label>
          </fieldset>
        ))}
        <fieldset className="rounded border border-neutral-200 p-3">
          <legend className="px-1 text-sm font-medium">{translate(locale, "specifications")}</legend>
          {specs.map((spec, index) => (
            <div key={index} className="mt-3 grid gap-2 sm:grid-cols-2">
              <input aria-label={`${translate(locale, "name")} RU`} value={spec.name_ru} onChange={(event) => updateSpec(index, "name_ru", event.target.value)} className={field} />
              <input aria-label={`${translate(locale, "description")} RU`} value={spec.value_ru} onChange={(event) => updateSpec(index, "value_ru", event.target.value)} className={field} />
              <input aria-label={`${translate(locale, "name")} UZ`} value={spec.name_uz} onChange={(event) => updateSpec(index, "name_uz", event.target.value)} className={field} />
              <input aria-label="UZ" value={spec.value_uz} onChange={(event) => updateSpec(index, "value_uz", event.target.value)} className={field} />
              <input aria-label={`${translate(locale, "name")} EN`} value={spec.name_en} onChange={(event) => updateSpec(index, "name_en", event.target.value)} className={field} />
              <input aria-label="EN" value={spec.value_en} onChange={(event) => updateSpec(index, "value_en", event.target.value)} className={field} />
              <button type="button" className="text-left text-sm underline" onClick={() => setSpecs(specs.filter((_, item) => item !== index))}>
                {translate(locale, "removeSpec")}
              </button>
            </div>
          ))}
          <button
            type="button"
            className="mt-3 text-sm underline"
            onClick={() =>
              setSpecs([...specs, { sort_order: specs.length, name_ru: "", value_ru: "", name_uz: "", value_uz: "", name_en: "", value_en: "" }])
            }
          >
            {translate(locale, "addSpec")}
          </button>
        </fieldset>
        {message ? (
          <p role="alert" className="text-sm text-red-700">
            {message}
          </p>
        ) : null}
        {saved ? <p className="text-sm text-green-800">{translate(locale, "saved")}</p> : null}
        <div className="flex flex-wrap gap-2">
          <button type="submit" className="rounded bg-neutral-900 px-4 py-2 text-sm text-white">
            {translate(locale, "save")}
          </button>
          {productId !== undefined ? (
            <button type="button" onClick={archive} className="rounded border border-neutral-300 px-4 py-2 text-sm">
              {translate(locale, "archive")}
            </button>
          ) : null}
        </div>
      </form>
      {source ? (
        <aside className="mt-6 rounded border border-neutral-200 bg-white p-3 text-sm">
          <h2 className="font-medium">{translate(locale, "provenance")}</h2>
          <p>
            {source.source_code} / {source.source_worksheet} / {source.source_row}
          </p>
          <p>
            {source.source_price_kind}
            {source.source_price_amount ? ` ${source.source_price_amount}` : ""}
          </p>
          {source.internal_note ? (
            <p>
              {translate(locale, "internalNote")}: {source.internal_note}
            </p>
          ) : null}
        </aside>
      ) : null}
      {productId !== undefined ? (
        <section className="mt-6">
          <h2 className="text-lg font-semibold">{translate(locale, "images")}</h2>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2">
            {images.map((image) => (
              <li key={image.id} className="rounded border border-neutral-200 bg-white p-3">
                {/* Catalog images are same-origin media objects. */}
                <img src={image.url} alt={image.alt_text ?? ""} className="h-32 w-full object-contain" />
                {image.is_primary ? <p className="mt-2 text-sm">{translate(locale, "primary")}</p> : null}
                <div className="mt-2 flex gap-3 text-sm">
                  <button type="button" className="underline" onClick={() => makePrimary(image.id)}>
                    {translate(locale, "makePrimary")}
                  </button>
                  <button type="button" className="underline" onClick={() => removeImage(image.id)}>
                    {translate(locale, "removeImage")}
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <form onSubmit={uploadImage} className="mt-3 flex flex-wrap items-end gap-2">
            <label className="text-sm">
              {translate(locale, "uploadImage")}
              <input name="file" type="file" accept="image/png,image/jpeg,image/webp" required className="mt-1 block" />
            </label>
            <label className="text-sm">
              {translate(locale, "altText")}
              <input name="alt_text" value={alt} onChange={(event) => setAlt(event.target.value)} className={field} />
            </label>
            <button type="submit" className="rounded border border-neutral-300 px-3 py-2 text-sm">
              {translate(locale, "save")}
            </button>
          </form>
        </section>
      ) : null}
    </section>
  );

  function updateSpec(index: number, key: keyof Spec, value: string) {
    setSpecs(specs.map((spec, item) => (item === index ? { ...spec, [key]: value } : spec)));
  }
}
