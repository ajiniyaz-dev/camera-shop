"use client";

import { useState } from "react";

import { CameraGlyph, focusLight } from "@/components/public/brand-mark";
import { ProductPhoto } from "@/components/public/product-photo";
import type { PublicImage } from "@/lib/public-api";

const stageClass = "flex h-[15.5rem] w-full items-center justify-center p-2 sm:h-[18rem] sm:p-3 md:h-[22rem] lg:h-[26rem]";

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
      <div className={`${stageClass} flex-col gap-2 px-4 text-center text-sm text-navy/70`}>
        <CameraGlyph className="h-10 w-10 text-navy" />
        {emptyLabel}
      </div>
    );
  }
  const image = images[Math.min(active, images.length - 1)];
  return (
    <div className="flex flex-col gap-2">
      <div className={stageClass}>
        <ProductPhoto src={image.url} alt={image.alt} width={image.width} height={image.height} />
      </div>
      {images.length > 1 ? (
        <ul className="flex flex-wrap gap-2 px-2 pb-2" aria-label={label}>
          {images.map((item, index) => {
            const selected = index === active;
            return (
              <li key={item.url}>
                <button
                  type="button"
                  aria-label={item.alt}
                  aria-pressed={selected}
                  aria-current={selected ? "true" : undefined}
                  onClick={() => setActive(index)}
                  className={`relative h-14 w-14 overflow-hidden rounded-md border bg-white ${focusLight} ${
                    selected ? "border-brand ring-1 ring-brand/40" : "border-line hover:border-brand/50"
                  }`}
                >
                  <span className="absolute inset-1 flex items-center justify-center">
                    <ProductPhoto src={item.url} alt="" width={item.width} height={item.height} />
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
