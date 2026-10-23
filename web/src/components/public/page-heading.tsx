import Link from "next/link";

import { focusLight } from "@/components/public/brand-mark";

export function PageHeading({
  title,
  description,
  action,
  count,
}: {
  title: string;
  description?: string | null;
  action?: { href: string; label: string };
  count?: number;
}) {
  return (
    <header className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <div aria-hidden="true" className="accent-rail mb-2" />
        <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
          {title}
          {typeof count === "number" ? <span className="ml-2 text-base font-normal text-mute">({count})</span> : null}
        </h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-mute">{description}</p> : null}
      </div>
      {action ? (
        <Link href={action.href} className={`inline-flex min-h-11 shrink-0 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
          {action.label}
        </Link>
      ) : null}
    </header>
  );
}
