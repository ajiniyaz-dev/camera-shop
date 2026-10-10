"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminJson, ApiError } from "@/lib/admin-api";
import { translate, type MessageKey } from "@/lib/i18n";

type Job = {
  id: number;
  status: string;
  replace_prices: boolean;
  publish_new_products: boolean;
  error_message: string | null;
  summary: {
    combined?: Record<string, number>;
    rejected_files?: Array<{ original_filename?: string; code?: string }>;
    result?: { counts?: Record<string, number> };
  };
  files: Array<{ id: number; source_code: string; original_filename: string; validation_status: string; validation_errors: unknown[] }>;
};
type PriceProposal = {
  kind?: string | null;
  public_status?: string | null;
  public_amount?: string | number | null;
  currency?: string | null;
};
type Proposal = {
  model_display?: string | null;
  option_label?: string | null;
  description?: string | null;
  brand?: string | null;
  category_name?: string | null;
  heading_text?: string | null;
  internal_note?: string | null;
  price?: PriceProposal | null;
  field_changes?: string[];
  field_resolutions?: Record<string, string>;
};
type Current = {
  model_display: string;
  option_label: string | null;
  brand: string | null;
  category: string | null;
  description: string | null;
  public_price_status: string;
  public_price_amount: string | null;
  locks: Record<string, boolean>;
};
type Row = {
  id: number;
  worksheet_name: string;
  source_row: number;
  classification: string;
  action: string;
  resolution: string;
  matched_product_id: number | null;
  messages: Array<{ code?: string }>;
  proposal: Proposal | null;
  current: Current | null;
  applied: boolean;
};
type Asset = {
  id: number;
  link_status: string;
  worksheet: string | null;
  anchor_row: number | null;
  excluded: boolean;
  anchor_model: string | null;
};
type Resolution = "keep_current" | "accept_excel" | "exclude";

const resolutionLabel: Record<Resolution, MessageKey> = {
  keep_current: "keepCurrent",
  accept_excel: "acceptExcel",
  exclude: "exclude",
};

const fieldLabel: Record<string, MessageKey> = {
  model_display: "model",
  option_label: "option",
  description: "description",
  brand: "brand",
  category: "category",
  category_name: "category",
  public_price: "price",
  source_price_kind: "provenance",
};

function resolutionsFor(row: Row): Resolution[] {
  if (row.classification !== "product" && row.classification !== "service") {
    return ["exclude"];
  }
  if (row.action === "conflict") {
    return ["keep_current", "exclude"];
  }
  return ["keep_current", "accept_excel", "exclude"];
}

function textValue(value: string | number | null | undefined, emptyLabel: string): string {
  if (value === null || value === undefined || value === "") {
    return emptyLabel;
  }
  return String(value);
}

function incomingValue(proposal: Proposal | null, field: string, emptyLabel: string): string {
  if (!proposal) {
    return emptyLabel;
  }
  if (field === "public_price") {
    const price = proposal.price;
    if (!price) {
      return emptyLabel;
    }
    const amount = price.public_amount === null || price.public_amount === undefined || price.public_amount === ""
      ? ""
      : ` ${price.public_amount}${price.currency ? ` ${price.currency}` : ""}`;
    return `${textValue(price.public_status, emptyLabel)}${amount} (${textValue(price.kind, emptyLabel)})`;
  }
  if (field === "category") {
    return textValue(proposal.category_name, emptyLabel);
  }
  const value = proposal[field as keyof Proposal];
  return typeof value === "string" || typeof value === "number" ? textValue(value, emptyLabel) : emptyLabel;
}

function currentValue(current: Current | null, field: string, emptyLabel: string): string | null {
  if (!current) {
    return null;
  }
  if (field === "public_price") {
    const amount = current.public_price_amount ? ` ${current.public_price_amount}` : "";
    return `${current.public_price_status}${amount}`;
  }
  if (field === "category") {
    return textValue(current.category, emptyLabel);
  }
  if (field === "model_display") {
    return textValue(current.model_display, emptyLabel);
  }
  if (field === "option_label") {
    return textValue(current.option_label, emptyLabel);
  }
  if (field === "description") {
    return textValue(current.description, emptyLabel);
  }
  if (field === "brand") {
    return textValue(current.brand, emptyLabel);
  }
  return null;
}

function overwrittenFields(row: Row): string[] {
  const resolutions = row.proposal?.field_resolutions ?? {};
  return Object.entries(resolutions)
    .filter(([, value]) => value === "keep_current")
    .map(([field]) => field);
}

export default function ImportDetailPage() {
  const locale = useAdminLocale();
  const params = useParams<{ id: string }>();
  const jobId = params.id;
  const [job, setJob] = useState<Job | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [assetPage, setAssetPage] = useState(1);
  const [assetTotal, setAssetTotal] = useState(0);
  const [action, setAction] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  function reload() {
    const query = new URLSearchParams({ page: String(page), page_size: "20" });
    if (action) {
      query.set("action", action);
    }
    const assetsQuery = new URLSearchParams({ page: String(assetPage), page_size: "20" });
    setLoading(true);
    Promise.all([
      adminJson<Job>(`/api/admin/imports/${jobId}`),
      adminJson<{ rows: Row[]; total: number }>(`/api/admin/imports/${jobId}/rows?${query}`),
      adminJson<{ assets: Asset[]; total: number }>(`/api/admin/imports/${jobId}/assets?${assetsQuery}`),
    ])
      .then(([nextJob, nextRows, nextAssets]) => {
        setJob(nextJob);
        setRows(nextRows.rows);
        setTotal(nextRows.total);
        setAssets(nextAssets.assets);
        setAssetTotal(nextAssets.total);
        setMessage("");
      })
      .catch((error: unknown) => {
        setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
      })
      .finally(() => setLoading(false));
  }

  useEffect(reload, [jobId, locale, page, assetPage, action]);

  async function resolve(row: Row, resolution: string) {
    if (resolution === "accept_excel") {
      const fields = overwrittenFields(row);
      const named = fields.map((field) => translate(locale, fieldLabel[field] ?? "price")).join(", ");
      const prompt = named
        ? `${translate(locale, "acceptExcelConfirm")}\n${translate(locale, "overwriteFields")}: ${named}`
        : translate(locale, "acceptExcelConfirm");
      if (!window.confirm(prompt)) {
        return;
      }
    }
    setMessage("");
    try {
      await adminJson(`/api/admin/imports/${jobId}/rows/${row.id}`, { method: "PATCH" }, { resolution });
      reload();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  async function excludeAsset(asset: Asset) {
    setMessage("");
    try {
      await adminJson(`/api/admin/imports/${jobId}/assets/${asset.id}/exclusion`, { method: "POST" }, { excluded: !asset.excluded });
      reload();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  async function apply() {
    setMessage("");
    try {
      await adminJson(`/api/admin/imports/${jobId}/apply`, { method: "POST" }, { confirm: true });
      setConfirm(false);
      reload();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  async function reject() {
    if (!window.confirm(translate(locale, "confirmReject"))) {
      return;
    }
    setMessage("");
    try {
      await adminJson(`/api/admin/imports/${jobId}/reject`, { method: "POST" });
      reload();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  if (!job) {
    return <p>{loading ? translate(locale, "loading") : message || translate(locale, "error")}</p>;
  }

  const preview = job.status === "preview";
  const emptyLabel = translate(locale, "emptyValue");

  return (
    <section>
      <p className="text-sm">
        <Link href="/admin/imports" className="underline">{translate(locale, "back")}</Link>
      </p>
      <h1 className="mt-2 text-2xl font-semibold">
        {translate(locale, "jobStatus")}: {job.status}
      </h1>
      {job.status === "applied" ? <p className="mt-2 text-sm">{translate(locale, "appliedResult")}</p> : null}
      {job.status === "rejected" ? <p className="mt-2 text-sm">{translate(locale, "rejectedJob")}</p> : null}
      {job.status === "failed" ? <p className="mt-2 text-sm">{translate(locale, "failedJob")}</p> : null}
      {job.replace_prices ? <p className="mt-2 text-sm">{translate(locale, "replacePrices")}</p> : null}
      {job.error_message ? <p role="alert" className="mt-2 text-sm text-red-700">{job.error_message}</p> : null}
      {message ? <p role="alert" className="mt-2 text-sm text-red-700">{message}</p> : null}
      <h2 className="mt-6 font-medium">{translate(locale, "validation")}</h2>
      <ul className="mt-2 text-sm">
        {job.files.map((file) => (
          <li key={file.id}>
            {file.source_code}: {file.original_filename} ({file.validation_status})
            {(file.validation_errors ?? []).length > 0 ? <span className="block text-red-700">{JSON.stringify(file.validation_errors)}</span> : null}
          </li>
        ))}
        {(job.summary.rejected_files ?? []).map((file, index) => (
          <li key={index}>
            {file.original_filename}: {file.code}
          </li>
        ))}
      </ul>
      {job.summary.result?.counts ? (
        <p className="mt-3 text-sm">{JSON.stringify(job.summary.result.counts)}</p>
      ) : null}
      {job.summary.combined ? <p className="mt-2 text-sm">{JSON.stringify(job.summary.combined)}</p> : null}
      <h2 className="mt-6 font-medium">{translate(locale, "rows")}</h2>
      <label className="mt-2 block text-sm">
        {translate(locale, "rowFilter")}
        <select
          value={action}
          onChange={(event) => {
            setAction(event.target.value);
            setPage(1);
          }}
          className="ml-2 rounded border border-neutral-300 px-2 py-1"
        >
          <option value="">{translate(locale, "all")}</option>
          <option value="conflict">conflict</option>
          <option value="possible_match">possible_match</option>
          <option value="update">update</option>
          <option value="insert">insert</option>
        </select>
      </label>
      {loading ? <p className="mt-3 text-sm">{translate(locale, "loading")}</p> : null}
      {rows.length === 0 ? <p className="mt-3 text-sm">{translate(locale, "empty")}</p> : null}
      <ul className="mt-2 divide-y rounded border border-neutral-200 bg-white">
        {rows.map((row) => {
          const proposal = row.proposal;
          const changes = proposal?.field_changes ?? [];
          const resolutions = proposal?.field_resolutions ?? {};
          const priceLocked = Boolean(row.current?.locks.public_price) && (changes.includes("public_price") || row.messages.some((item) => item.code === "replace_prices"));
          return (
            <li key={row.id} className={`grid gap-3 px-3 py-3 text-sm sm:grid-cols-[1fr_auto] ${row.resolution === "pending" ? "bg-amber-50" : ""}`}>
              <div>
                <p className="font-medium">
                  {textValue(proposal?.model_display ?? proposal?.heading_text, emptyLabel)} · {row.worksheet_name} #{row.source_row}
                </p>
                <p>
                  {row.classification} · {row.action} · {row.resolution}
                  {row.matched_product_id ? ` · ${translate(locale, "products")} #${row.matched_product_id}` : ""}
                </p>
                {row.action === "exclude" ? <p>{translate(locale, "excludedRow")}</p> : null}
                {row.resolution === "pending" ? <p>{translate(locale, "pendingReview")}</p> : null}
                <p className="text-neutral-600">{row.messages.map((item) => item.code).filter(Boolean).join(", ")}</p>
                {proposal && (row.classification === "product" || row.classification === "service") ? (
                  <p className="mt-2">
                    {translate(locale, "incoming")}: {translate(locale, "price")} {incomingValue(proposal, "public_price", emptyLabel)}; {translate(locale, "brand")} {incomingValue(proposal, "brand", emptyLabel)}; {translate(locale, "category")} {incomingValue(proposal, "category", emptyLabel)}; {translate(locale, "description")} {incomingValue(proposal, "description", emptyLabel)}
                  </p>
                ) : null}
                {priceLocked ? (
                  <p className="mt-2 rounded border border-amber-300 bg-amber-50 p-2">
                    <span className="font-medium">{translate(locale, "lockedPrice")}. </span>
                    {translate(locale, "protectedUntilOverride")}
                    {" "}
                    {translate(locale, "currentValue")}: {currentValue(row.current, "public_price", emptyLabel)}. {translate(locale, "incoming")}: {incomingValue(proposal, "public_price", emptyLabel)}.
                  </p>
                ) : null}
                {changes.length > 0 ? (
                  <div className="mt-2">
                    <p className="font-medium">{translate(locale, "proposedChanges")}</p>
                    <ul className="mt-1 space-y-1">
                      {changes.map((field) => (
                        <li key={field}>
                          {translate(locale, fieldLabel[field] ?? "details")}: {translate(locale, "currentValue")} {currentValue(row.current, field, emptyLabel) ?? emptyLabel}; {translate(locale, "incoming")} {incomingValue(proposal, field, emptyLabel)}; {resolutions[field] ?? row.resolution}
                          {row.current?.locks[field] ? ` · ${translate(locale, "locked")}` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {proposal?.internal_note ? (
                  <p className="mt-2">
                    {translate(locale, "internalNote")}: {proposal.internal_note}
                  </p>
                ) : null}
              </div>
              {preview ? (
                <div className="flex flex-wrap gap-2">
                  {resolutionsFor(row).map((resolution) => (
                    <button key={resolution} type="button" className="underline" onClick={() => resolve(row, resolution)}>
                      {translate(locale, resolutionLabel[resolution])}
                    </button>
                  ))}
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
      <div className="mt-3 flex gap-2 text-sm">
        <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded border px-2 py-1 disabled:opacity-40">{translate(locale, "previous")}</button>
        <span>{translate(locale, "page")} {page} / {Math.max(1, Math.ceil(total / 20))}</span>
        <button type="button" disabled={page * 20 >= total} onClick={() => setPage(page + 1)} className="rounded border px-2 py-1 disabled:opacity-40">{translate(locale, "next")}</button>
      </div>
      <h2 className="mt-6 font-medium">{translate(locale, "assets")}</h2>
      <p className="mt-1 text-sm text-neutral-600">{translate(locale, "assetHint")}</p>
      {assets.length === 0 ? <p className="mt-2 text-sm">{translate(locale, "noAssets")}</p> : null}
      <ul className="mt-2 text-sm">
        {assets.map((asset) => (
          <li key={asset.id} className="flex flex-wrap items-center gap-3 border-b border-neutral-200 py-2">
            <span>{asset.link_status}</span>
            <span>{asset.worksheet} #{asset.anchor_row}</span>
            <span>{textValue(asset.anchor_model, emptyLabel)}</span>
            {asset.excluded ? <span>{translate(locale, "exclude")}</span> : null}
            {preview ? (
              <button type="button" className="underline" onClick={() => excludeAsset(asset)}>
                {asset.excluded ? translate(locale, "cancel") : translate(locale, "exclude")}
              </button>
            ) : null}
          </li>
        ))}
      </ul>
      <div className="mt-3 flex gap-2 text-sm">
        <button type="button" disabled={assetPage <= 1} onClick={() => setAssetPage(assetPage - 1)} className="rounded border px-2 py-1 disabled:opacity-40">{translate(locale, "previous")}</button>
        <span>{translate(locale, "page")} {assetPage} / {Math.max(1, Math.ceil(assetTotal / 20))}</span>
        <button type="button" disabled={assetPage * 20 >= assetTotal} onClick={() => setAssetPage(assetPage + 1)} className="rounded border px-2 py-1 disabled:opacity-40">{translate(locale, "next")}</button>
      </div>
      {preview ? (
        <div className="mt-6 space-y-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={confirm} onChange={(event) => setConfirm(event.target.checked)} />
            {translate(locale, "confirmApply")}
          </label>
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={!confirm} onClick={apply} className="rounded bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-40">
              {translate(locale, "apply")}
            </button>
            <button type="button" onClick={reject} className="rounded border border-neutral-300 px-4 py-2 text-sm">
              {translate(locale, "reject")}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
