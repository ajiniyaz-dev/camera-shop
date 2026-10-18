/** Guards for admin screens that must not treat an unloaded list or product as empty data. */

export function canSaveLoadedProduct(productId: number | undefined, loaded: boolean): boolean {
  return productId === undefined || loaded;
}

export function listStatus(
  loading: boolean,
  failed: boolean,
  count: number,
): "loading" | "error" | "empty" | "ready" {
  if (loading && count === 0) {
    return "loading";
  }
  if (failed && count === 0) {
    return "error";
  }
  if (count === 0) {
    return "empty";
  }
  return "ready";
}
