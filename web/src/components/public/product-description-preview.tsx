"use client";

import { useState } from "react";

import { descriptionPreview } from "@/lib/product-description";

export function ProductDescriptionPreview({
  description,
  readMoreLabel,
  showLessLabel,
}: {
  description: string | null | undefined;
  readMoreLabel: string;
  showLessLabel: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const preview = descriptionPreview(description, expanded);
  const canToggle = descriptionPreview(description, false).hasMore;
  if (!preview.text) return null;

  return (
    <div className="mt-3 text-sm leading-6 text-ink/75">
      <p className="break-words">{preview.text}</p>
      {canToggle ? (
        <button
          type="button"
          aria-expanded={expanded}
          onClick={() => setExpanded((value) => !value)}
          className="mt-1 rounded-sm font-medium text-brand underline decoration-brand/40 underline-offset-4 hover:text-navy focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal focus-visible:ring-offset-2"
        >
          {expanded ? showLessLabel : readMoreLabel}
        </button>
      ) : null}
    </div>
  );
}
