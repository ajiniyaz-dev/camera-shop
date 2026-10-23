"use client";

import { ChevronDown } from "lucide-react";
import { useId, useState, type ReactNode, type ToggleEvent } from "react";

import { focusLight } from "@/components/public/brand-mark";

export function CatalogFilterSection({
  id,
  title,
  defaultOpen = true,
  extra,
  children,
}: {
  id?: string;
  title: string;
  defaultOpen?: boolean;
  extra?: ReactNode;
  children: ReactNode;
}) {
  const generatedId = useId();
  const panelId = id ?? `${generatedId}-panel`;
  const [open, setOpen] = useState(defaultOpen);

  function onToggle(event: ToggleEvent<HTMLDetailsElement>) {
    setOpen(event.currentTarget.open);
  }

  return (
    <details open={open} onToggle={onToggle} className="group/section">
      <summary
        aria-expanded={open}
        aria-controls={panelId}
        className={`flex min-h-10 cursor-pointer list-none items-center gap-2 rounded-md px-2.5 text-[13px] font-semibold tracking-tight text-navy hover:bg-sky/10 [&::-webkit-details-marker]:hidden ${focusLight}`}
      >
        <span className="min-w-0 flex-1 truncate">{title}</span>
        {extra ? <span className="shrink-0">{extra}</span> : null}
        <ChevronDown
          aria-hidden="true"
          className="h-4 w-4 shrink-0 text-navy/70 transition-transform duration-200 ease-out group-open/section:rotate-180 motion-reduce:transition-none"
          strokeWidth={2}
        />
      </summary>
      <div id={panelId} className="catalog-panel-in">
        {children}
      </div>
    </details>
  );
}
