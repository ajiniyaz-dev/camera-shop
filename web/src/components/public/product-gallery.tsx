"use client";

import { useState } from "react";

import { CameraGlyph, focusLight } from "@/components/public/brand-mark";
import { ProductPhoto } from "@/components/public/product-photo";
import type { PublicImage } from "@/lib/public-api";

export function ProductGallery({
  images,
  emptyLabel,
  label,
}: {
  images: PublicImage[];
  emptyLabel: string;
  label: string;
}) {
  const [active, setActive] = useState(0);
  if (!images.length) {
    return (
      <div className="flex h-80 flex-col items-center justify-center gap-3 border border-navy/10 bg-mist px-4 text-center text-sm text-navy/70">
        <CameraGlyph className="h-12 w-12 text-navy" />
        {emptyLabel}
      </div>
    );
  }
  const image = images[Math.min(active, images.length - 1)];
  return (
    <div className="space-y-3">
      <div className="flex min-h-80 items-center justify-center border border-navy/10 bg-mist p-4">
        <ProductPhoto src={image.url} alt={image.alt} width={image.width} height={image.height} limit="gallery" />
      </div>
      {images.length > 1 ? (
        <ul className="grid grid-cols-4 gap-2 sm:grid-cols-5" aria-label={label}>
          {images.map((item, index) => {
            const selected = index === active;
            return (
              <li key={item.url}>
                <button
                  type="button"
                  aria-label={item.alt}
                  aria-pressed={selected}
                  onClick={() => setActive(index)}
                  className={`flex h-20 w-full items-center justify-center border bg-mist p-1 ${focusLight} ${
                    selected ? "border-brand" : "border-navy/10 hover:border-brand/50"
                  }`}
                >
                  <ProductPhoto src={item.url} alt="" width={item.width} height={item.height} />
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
