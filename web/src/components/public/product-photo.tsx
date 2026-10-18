import { productPhotoAttributes, productPhotoClassName } from "@/lib/product-photo";

export function ProductPhoto({
  src,
  alt,
  width,
  height,
  limit = "frame",
}: {
  src: string;
  alt: string;
  width?: number | null;
  height?: number | null;
  limit?: "frame" | "gallery";
}) {
  return <img src={src} alt={alt} {...productPhotoAttributes(width, height)} className={productPhotoClassName(limit)} />;
}
