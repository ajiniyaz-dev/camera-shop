/** Layout for a catalog photo. Missing dimensions stay unset so a tiny bitmap is not given a large stand-in size. */

export function productPhotoAttributes(
  width: number | null | undefined,
  height: number | null | undefined,
): { width?: number; height?: number } {
  if (typeof width === "number" && width > 0 && typeof height === "number" && height > 0) {
    return { width, height };
  }
  return {};
}

export function productPhotoClassName(limit: "frame" | "gallery" = "frame"): string {
  const cap = limit === "gallery" ? "max-h-[32rem] max-w-full" : "max-h-full max-w-full";
  return `h-auto w-auto object-contain ${cap}`;
}
