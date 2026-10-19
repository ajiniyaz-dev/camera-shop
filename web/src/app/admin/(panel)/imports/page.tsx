"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminFetch, adminJson, errorMessage } from "@/lib/admin-api";
import { translate, type MessageKey } from "@/lib/i18n";

type Job = { id: number; status: string; replace_prices: boolean; publish_new_products: boolean };

type PreviewSummary = {
  sources?: Array<{ original_filename?: string; counts?: Record<string, number> }>;
  rejected_files?: unknown[];
  combined?: Record<string, number>;
};

type PreviewResult = {
  id: number;
  status: string;
  summary?: PreviewSummary;
};

type Phase = "idle" | "processing" | "success" | "failure";

const ROW_KEYS = ["product", "service", "heading", "blank", "stray", "invalid"] as const;

function countOf(record: Record<string, number> | undefined, key: string): number | null {
  const value = record?.[key];
  return typeof value === "number" ? value : null;
}

function rowCount(combined: Record<string, number> | undefined): number | null {
  const values = ROW_KEYS.map((key) => countOf(combined, key)).filter((value): value is number => value !== null);
  return values.length === 0 ? null : values.reduce((total, value) => total + value, 0);
}

function conflictCount(combined: Record<string, number> | undefined): number | null {
  const conflict = countOf(combined, "conflict");
  const possible = countOf(combined, "possible_match");
  if (conflict === null && possible === null) {
    return null;
  }
  return (conflict ?? 0) + (possible ?? 0);
}

function Spinner() {
  return (
    <span
      aria-hidden="true"
      className="inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-current border-r-transparent motion-reduce:animate-none"
    />
  );
}

export default function ImportsPage() {
  const locale = useAdminLocale();
  const pendingRef = useRef(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [phase, setPhase] = useState<Phase>("idle");
  const [failureDetail, setFailureDetail] = useState("");
  const [result, setResult] = useState<PreviewResult | null>(null);
  const [replacePrices, setReplacePrices] = useState(false);
  const [publishNew, setPublishNew] = useState(true);
  const [hikvisionOverride, setHikvisionOverride] = useState("");
  const [ezvizOverride, setEzvizOverride] = useState("");
  const pending = phase === "processing";

  function reload() {
    adminJson<{ jobs: Job[] }>("/api/admin/imports").then((body) => setJobs(body.jobs));
  }

  useEffect(reload, []);

  async function upload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pendingRef.current) {
      return;
    }
    pendingRef.current = true;
    setPhase("processing");
    setFailureDetail("");
    setResult(null);
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
    try {
      const response = await adminFetch("/api/admin/imports", { method: "POST", body: data });
      if (!response.ok) {
        const message = await errorMessage(response);
        setFailureDetail(/^\d{3}$/.test(message) ? "" : message);
        setPhase("failure");
        return;
      }
      const created = (await response.json()) as PreviewResult;
      setResult(created);
      setPhase("success");
      reload();
    } catch {
      setFailureDetail("");
      setPhase("failure");
    } finally {
      pendingRef.current = false;
    }
  }

  const combined = result?.summary?.combined;
  const workbookCount = Array.isArray(result?.summary?.sources) ? result.summary.sources.length : null;
  const rows = rowCount(combined);
  const products = countOf(combined, "product");
  const invalid = countOf(combined, "invalid");
  const rejected = Array.isArray(result?.summary?.rejected_files) ? result.summary.rejected_files.length : null;
  const validation =
    invalid === null && rejected === null ? null : (invalid ?? 0) + (rejected ?? 0);
  const conflicts = conflictCount(combined);
  const images = countOf(combined, "images_extracted");
  const facts: Array<{ key: MessageKey; value: number }> = [];
  if (workbookCount !== null) {
    facts.push({ key: "workbooksProcessed", value: workbookCount });
  }
  if (rows !== null) {
    facts.push({ key: "rowsDiscovered", value: rows });
  }
  if (products !== null) {
    facts.push({ key: "productsDiscovered", value: products });
  }
  if (validation !== null) {
    facts.push({ key: "validationIssues", value: validation });
  }
  if (conflicts !== null) {
    facts.push({ key: "conflictsFound", value: conflicts });
  }
  if (images !== null) {
    facts.push({ key: "imagesExtracted", value: images });
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">{translate(locale, "imports")}</h1>
      <form
        onSubmit={upload}
        aria-busy={pending}
        aria-describedby={phase === "idle" ? undefined : "import-preview-status"}
        className="mt-4 space-y-3 rounded border border-line bg-white p-4"
      >
        <h2 className="font-medium">{translate(locale, "uploadWorkbooks")}</h2>
        <label className="block text-sm">
          {translate(locale, "hikvisionFile")}
          <input name="hikvision" type="file" accept=".xlsx" disabled={pending} className="mt-1 block" />
        </label>
        <label className="block text-sm">
          {translate(locale, "override")}
          <select
            value={hikvisionOverride}
            onChange={(event) => setHikvisionOverride(event.target.value)}
            disabled={pending}
            className="mt-1 rounded border px-2 py-1"
          >
            <option value="">{translate(locale, "auto")}</option>
            <option value="hikvision">Hikvision</option>
            <option value="ezviz">EZVIZ</option>
          </select>
        </label>
        <label className="block text-sm">
          {translate(locale, "ezvizFile")}
          <input name="ezviz" type="file" accept=".xlsx" disabled={pending} className="mt-1 block" />
        </label>
        <label className="block text-sm">
          {translate(locale, "override")}
          <select
            value={ezvizOverride}
            onChange={(event) => setEzvizOverride(event.target.value)}
            disabled={pending}
            className="mt-1 rounded border px-2 py-1"
          >
            <option value="">{translate(locale, "auto")}</option>
            <option value="hikvision">Hikvision</option>
            <option value="ezviz">EZVIZ</option>
          </select>
        </label>
        <p className="text-sm text-mute">{translate(locale, "sourceOverrideHint")}</p>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={replacePrices}
            disabled={pending}
            onChange={(event) => setReplacePrices(event.target.checked)}
          />
          {translate(locale, "replacePrices")}
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={publishNew}
            disabled={pending}
            onChange={(event) => setPublishNew(event.target.checked)}
          />
          {translate(locale, "publishNew")}
        </label>
        {phase === "processing" ? (
          <div
            id="import-preview-status"
            role="status"
            className="flex items-center gap-2 rounded border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-950"
          >
            <Spinner />
            <span>{translate(locale, "previewPreparing")}</span>
          </div>
        ) : null}
        {phase === "success" && result ? (
          <div
            id="import-preview-status"
            role="status"
            className="space-y-2 rounded border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-950"
          >
            <p className="flex items-center gap-2 font-medium">
              <span aria-hidden="true">✓</span>
              {translate(locale, "previewReady")}
            </p>
            <p>
              <Link href={`/admin/imports/${result.id}`} className="underline">
                #{result.id}
              </Link>
              {result.status ? <span> · {translate(locale, "jobStatus")}: {result.status}</span> : null}
            </p>
            {facts.length > 0 ? (
              <ul className="grid gap-1 sm:grid-cols-2">
                {facts.map((fact) => (
                  <li key={fact.key}>
                    {translate(locale, fact.key)}: {fact.value}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
        {phase === "failure" ? (
          <div
            id="import-preview-status"
            role="alert"
            className="space-y-1 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
          >
            <p>{translate(locale, "previewFailed")}</p>
            {failureDetail ? <p>{failureDetail}</p> : null}
            <p>{translate(locale, "previewRetry")}</p>
          </div>
        ) : null}
        <button
          type="submit"
          disabled={pending}
          className="btn-primary disabled:opacity-70"
        >
          {pending ? <Spinner /> : null}
          {pending ? translate(locale, "generatingPreview") : translate(locale, "preview")}
        </button>
      </form>
      {jobs.length === 0 ? <p className="mt-6 text-sm">{translate(locale, "noJobs")}</p> : null}
      <ul className="mt-4 divide-y rounded border border-line bg-white">
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
