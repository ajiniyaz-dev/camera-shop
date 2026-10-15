export type AdminCategory = {
  id: number;
  parent_id: number | null;
  name_ru: string | null;
  name_uz: string | null;
  name_en: string | null;
  is_published: boolean;
};

export class CategoryListError extends Error {
  constructor() {
    super("The category list could not be read.");
    this.name = "CategoryListError";
  }
}

function textOrNull(value: unknown): string | null {
  if (value === null) {
    return null;
  }
  if (typeof value === "string") {
    return value;
  }
  throw new CategoryListError();
}

function category(value: unknown): AdminCategory {
  if (value === null || typeof value !== "object") {
    throw new CategoryListError();
  }
  const row = value as Record<string, unknown>;
  if (typeof row.id !== "number" || !Number.isInteger(row.id)) {
    throw new CategoryListError();
  }
  if (!(row.parent_id === null || (typeof row.parent_id === "number" && Number.isInteger(row.parent_id)))) {
    throw new CategoryListError();
  }
  if (typeof row.is_published !== "boolean") {
    throw new CategoryListError();
  }
  return {
    id: row.id,
    parent_id: row.parent_id,
    name_ru: textOrNull(row.name_ru),
    name_uz: textOrNull(row.name_uz),
    name_en: textOrNull(row.name_en),
    is_published: row.is_published,
  };
}

export function parseCategoryList(body: unknown): AdminCategory[] {
  if (body === null || typeof body !== "object" || !("categories" in body)) {
    throw new CategoryListError();
  }
  const categories = (body as { categories: unknown }).categories;
  if (!Array.isArray(categories)) {
    throw new CategoryListError();
  }
  return categories.map(category);
}

function apiFailure(error: unknown): { status: number; message: string } | null {
  if (!(error instanceof Error) || !("status" in error)) {
    return null;
  }
  const status = (error as { status?: unknown }).status;
  if (typeof status !== "number") {
    return null;
  }
  return { status, message: error.message };
}

export function categoryLoadFailure(error: unknown): "unauthorized" | "message" | "failed" {
  const failure = apiFailure(error);
  if (failure === null) {
    return "failed";
  }
  if (failure.status === 401) {
    return "unauthorized";
  }
  if (failure.message.trim()) {
    return "message";
  }
  return "failed";
}
