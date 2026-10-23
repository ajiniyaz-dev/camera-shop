"use client";

const field =
  "min-h-10 w-full rounded-md border border-line bg-white px-3 text-sm text-ink transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

export function CatalogSortSelect({
  label,
  name = "sort",
  defaultValue,
  options,
  grow = true,
}: {
  label: string;
  name?: string;
  defaultValue: string;
  options: Array<{ value: string; label: string }>;
  grow?: boolean;
}) {
  return (
    <label className={`flex min-w-0 items-center gap-2 text-xs font-medium text-mute ${grow ? "flex-1" : "shrink-0"}`}>
      {label}
      <select
        name={name}
        defaultValue={defaultValue}
        className={field}
        onChange={(event) => event.currentTarget.form?.requestSubmit()}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
