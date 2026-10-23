import { productPhotoAttributes, productPhotoClassName } from "@/lib/product-photo";

export function ProductPhoto({
  src,
  alt,
  width,
  height,
  limit = "frame",
  className,
}: {
  src: string;
  alt: string;
  width?: number | null;
  height?: number | null;
  limit?: "frame" | "gallery";
  className?: string;
}) {
  return <img src={src} alt={alt} {...productPhotoAttributes(width, height)} className={`${productPhotoClassName(limit)}${className ? ` ${className}` : ""}`} />;
}
