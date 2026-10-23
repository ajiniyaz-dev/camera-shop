"use client";

import { useId, useState, type ClipboardEvent, type FormEvent } from "react";

import { catalogPriceIssue, parseCatalogPrice, type CatalogPriceIssue } from "@/lib/catalog-price";

const field =
  "min-h-10 w-full rounded-md border border-line bg-white px-3 text-sm tabular-nums text-ink transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

export function CatalogPriceFields({
  minLabel,
  maxLabel,
  minPrice,
  maxPrice,
  invalidMessage,
  rangeMessage,
  initialIssue,
}: {
  minLabel: string;
  maxLabel: string;
  minPrice?: string;
  maxPrice?: string;
  invalidMessage: string;
  rangeMessage: string;
  initialIssue?: CatalogPriceIssue | null;
}) {
  const errorId = useId();
  const [issue, setIssue] = useState<CatalogPriceIssue | null>(initialIssue ?? null);
  const message = issue === "range" ? rangeMessage : issue === "invalid" ? invalidMessage : "";
  const invalidClass = issue ? " border-red-700" : "";

  function syncIssue(form: HTMLFormElement | null) {
    if (!form) return;
    const data = new FormData(form);
    const next = catalogPriceIssue(
      parseCatalogPrice(String(data.get("min_price") ?? "")),
      parseCatalogPrice(String(data.get("max_price") ?? "")),
    );
    setIssue(next);
    const text = next === "range" ? rangeMessage : next === "invalid" ? invalidMessage : "";
    const min = form.elements.namedItem("min_price") as HTMLInputElement | null;
    const max = form.elements.namedItem("max_price") as HTMLInputElement | null;
    min?.setCustomValidity(text);
    max?.setCustomValidity(text);
  }

  function onInput(event: FormEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    if (input.value === "" || /^\d{1,20}$/.test(input.value)) {
      input.dataset.lastValid = input.value;
      syncIssue(input.form);
      return;
    }
    input.value = input.dataset.lastValid ?? "";
    setIssue("invalid");
    input.setCustomValidity(invalidMessage);
  }

  function onPaste(event: ClipboardEvent<HTMLInputElement>) {
    const text = event.clipboardData.getData("text").trim();
    if (text === "" || /^\d{1,20}$/.test(text)) return;
    event.preventDefault();
    setIssue("invalid");
    event.currentTarget.setCustomValidity(invalidMessage);
  }

  return (
    <div className="mt-2 space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <label className="flex min-w-0 flex-col gap-1 text-xs font-medium text-mute">
          {minLabel}
          <input
            name="min_price"
            inputMode="numeric"
            autoComplete="off"
            pattern="[0-9]*"
            maxLength={20}
            defaultValue={minPrice ?? ""}
            data-last-valid={minPrice && /^\d{1,20}$/.test(minPrice) ? minPrice : ""}
            aria-invalid={Boolean(issue)}
            aria-describedby={message ? errorId : undefined}
            className={`${field}${invalidClass}`}
            onInput={onInput}
            onPaste={onPaste}
          />
        </label>
        <label className="flex min-w-0 flex-col gap-1 text-xs font-medium text-mute">
          {maxLabel}
          <input
            name="max_price"
            inputMode="numeric"
            autoComplete="off"
            pattern="[0-9]*"
            maxLength={20}
            defaultValue={maxPrice ?? ""}
            data-last-valid={maxPrice && /^\d{1,20}$/.test(maxPrice) ? maxPrice : ""}
            aria-invalid={Boolean(issue)}
            aria-describedby={message ? errorId : undefined}
            className={`${field}${invalidClass}`}
            onInput={onInput}
            onPaste={onPaste}
          />
        </label>
      </div>
      {message ? (
        <p id={errorId} role="alert" className="text-xs leading-5 text-red-800">
          {message}
        </p>
      ) : null}
    </div>
  );
}

export function preventInvalidPriceSubmit(
  event: FormEvent<HTMLFormElement>,
  messages: { invalid: string; range: string },
): boolean {
  const data = new FormData(event.currentTarget);
  const issue = catalogPriceIssue(
    parseCatalogPrice(String(data.get("min_price") ?? "")),
    parseCatalogPrice(String(data.get("max_price") ?? "")),
  );
  const min = event.currentTarget.elements.namedItem("min_price") as HTMLInputElement | null;
  const max = event.currentTarget.elements.namedItem("max_price") as HTMLInputElement | null;
  if (!issue) {
    min?.setCustomValidity("");
    max?.setCustomValidity("");
    return true;
  }
  event.preventDefault();
  const text = issue === "range" ? messages.range : messages.invalid;
  min?.setCustomValidity(text);
  max?.setCustomValidity(text);
  min?.reportValidity();
  return false;
}
