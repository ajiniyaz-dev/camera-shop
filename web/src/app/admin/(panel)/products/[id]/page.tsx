"use client";

import { useParams } from "next/navigation";

import { ProductEditor } from "@/components/admin/product-editor";

export default function EditProductPage() {
  const params = useParams<{ id: string }>();
  return <ProductEditor productId={Number(params.id)} />;
}
