/** Split catalog descriptions into readable blocks without inventing copy. */

const SENTENCE_BOUNDARY = /(?<=[.!?…])\s+(?=[A-ZА-ЯЁЎҚҒҲ])/;
const BULLET = /\s*[•·]\s*/;

function nonempty(parts: string[]): string[] {
  return parts.map((part) => part.trim()).filter(Boolean);
}

function splitBullets(text: string): string[] {
  if (!/[•·]/.test(text)) {
    return [text];
  }
  const parts = nonempty(text.split(BULLET));
  return parts.length > 1 ? parts : [text];
}

function splitSentences(text: string): string[] {
  const parts = nonempty(text.split(SENTENCE_BOUNDARY));
  return parts.length > 1 ? parts : [text];
}

function splitLine(text: string): string[] {
  return splitBullets(text).flatMap((part) => splitSentences(part));
}

/** Turn stored description text into paragraphs. Empty input yields no section. */
export function descriptionParagraphs(raw: string | null | undefined): string[] {
  if (!raw) {
    return [];
  }
  const text = raw.replace(/\r\n?/g, "\n").trim();
  if (!text) {
    return [];
  }
  const lines = nonempty(text.split(/\n+/));
  return lines.flatMap(splitLine);
}

/** Create a short, readable excerpt for the product details panel. */
export function descriptionPreview(
  raw: string | null | undefined,
  expanded: boolean,
): { text: string; hasMore: boolean } {
  const text = descriptionParagraphs(raw).join(" ");
  const limit = expanded ? 560 : 180;
  if (!text || text.length <= limit) {
    return { text, hasMore: false };
  }
  const clipped = text.slice(0, limit);
  const boundary = clipped.lastIndexOf(" ");
  return { text: `${clipped.slice(0, boundary > limit * 0.65 ? boundary : limit).trimEnd()}…`, hasMore: true };
}

/** Use a list only when stored text already reads as distinct short points. */
export function descriptionLayout(items: readonly string[]): "list" | "paragraphs" {
  if (items.length < 2) {
    return "paragraphs";
  }
  const labeled = items.filter((item) => /:\s*\S/.test(item)).length;
  if (labeled >= 2 && labeled >= items.length - 1) {
    return "list";
  }
  const short = items.filter((item) => item.length <= 110).length;
  if (items.length >= 3 && short >= Math.ceil(items.length * 0.75)) {
    return "list";
  }
  return "paragraphs";
}
