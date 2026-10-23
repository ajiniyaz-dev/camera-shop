import { descriptionLayout, descriptionParagraphs } from "@/lib/product-description";

export function ProductDescriptionBlock({
  id,
  title,
  text,
  showFallback,
  fallbackLabel,
}: {
  id?: string;
  title: string;
  text: string;
  showFallback: boolean;
  fallbackLabel: string;
}) {
  const paragraphs = descriptionParagraphs(text);
  if (!paragraphs.length) {
    return null;
  }
  const layout = descriptionLayout(paragraphs);
  return (
    <section id={id} className="rounded-lg border border-line bg-white p-5 sm:p-6">
      <div aria-hidden="true" className="accent-rail" />
      <h2 className="mt-2 text-base font-semibold tracking-tight text-navy sm:text-lg">{title}</h2>
      {showFallback ? <p className="mt-1 text-sm text-mute">{fallbackLabel}</p> : null}
      {layout === "list" ? (
        <ul className="mt-4 max-w-3xl space-y-2 text-[15px] leading-6 text-ink/85">
          {paragraphs.map((paragraph, index) => (
            <li key={`${index}-${paragraph.slice(0, 48)}`} className="flex gap-2.5">
              <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-teal" />
              <span>{paragraph}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-4 max-w-3xl space-y-3 text-[15px] leading-7 text-ink/85">
          {paragraphs.map((paragraph, index) => (
            <p key={`${index}-${paragraph.slice(0, 48)}`}>{paragraph}</p>
          ))}
        </div>
      )}
    </section>
  );
}
