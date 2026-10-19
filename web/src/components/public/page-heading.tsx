import Link from "next/link";

import { focusLight } from "@/components/public/brand-mark";

export function PageHeading({
  title,
  description,
  action,
}: {
  title: string;
  description?: string | null;
  action?: { href: string; label: string };
}) {
  return (
    <header className="flex flex-col gap-3 border-b border-line pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <div aria-hidden="true" className="accent-rail mb-2" />
        <h1 className="text-3xl font-semibold tracking-tight text-ink">{title}</h1>
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
