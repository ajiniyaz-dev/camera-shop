"use client";

import { useEffect, useState } from "react";

import { focusLight } from "@/components/public/brand-mark";
import { SelectionCartIcon } from "@/components/public/catalog-icons";
import { messages, type PublicLocale } from "@/lib/public-i18n";
import { addToSelection, readSelection, removeFromSelection, SELECTION_EVENT, writeSelection } from "@/lib/selection";

export function SelectionButton({ slug, locale }: { slug: string; locale: PublicLocale }) {
  const text = messages[locale];
  const [included, setIncluded] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const sync = () => setIncluded(readSelection().includes(slug));
    sync();
    window.addEventListener(SELECTION_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(SELECTION_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, [slug]);

  function change() {
    if (included) {
      writeSelection(removeFromSelection(readSelection(), slug));
      setNotice("");
      return;
    }
    const result = addToSelection(readSelection(), slug);
    if (result.status === "full") {
      setNotice(text.selectionFull);
      return;
    }
    writeSelection(result.slugs);
    setNotice("");
  }

  return (
    <span className="inline-flex w-full flex-col items-stretch gap-1 sm:w-auto">
      <button
        type="button"
        aria-pressed={included}
        onClick={change}
        className={`inline-flex min-h-11 w-full items-center justify-center gap-2 border px-4 text-sm font-medium transition-colors sm:w-auto sm:min-w-[13.5rem] ${focusLight} ${
          included
            ? "border-navy/20 bg-mist text-navy hover:border-brand"
            : "border-[#FF414D]/45 bg-white text-navy hover:border-[#FF414D] hover:bg-mist"
        }`}
      >
        <SelectionCartIcon />
        <span>{included ? text.removeFromSelection : text.addToSelection}</span>
      </button>
      {notice ? <span className="text-xs text-navy/70">{notice}</span> : null}
    </span>
  );
}
