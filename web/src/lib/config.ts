/**
 * Base URL for server-side calls from Next.js to FastAPI.
 * Set API_INTERNAL_URL in the environment. Do not prefix it with NEXT_PUBLIC_.
 * Browsers call same-origin /api through Nginx and do not use this value.
 */
export function getInternalApiUrl(): string {
  const value = process.env.API_INTERNAL_URL?.trim();
  if (!value) {
    throw new Error("API_INTERNAL_URL is not set");
  }
  return value.replace(/\/+$/, "");
}
