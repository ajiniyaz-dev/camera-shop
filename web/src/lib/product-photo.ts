/** Layout for a catalog photo. Missing dimensions stay unset so a tiny listing bitmap is not given a large stand-in size. */

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
  // Both placements constrain oversized files without enlarging small source images.
  void limit;
  return "h-auto w-auto max-h-full max-w-full object-contain";
}
