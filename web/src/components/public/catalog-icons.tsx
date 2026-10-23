import {
  BatteryCharging,
  Box,
  Building2,
  Cable,
  Camera,
  ChevronLeft,
  Folder,
  HardDrive,
  Hash,
  KeyRound,
  MonitorPlay,
  Network,
  Phone,
  Plug,
  Router,
  Server,
  ShoppingCart,
  Tag,
  Video,
  Volume2,
  Wrench,
  type LucideIcon,
  type LucideProps,
} from "lucide-react";

import { categoryMark, type CategoryMark } from "@/lib/home-category";

/** Shared with the header cart control and add-to-cart buttons. Do not recolor casually. */
export const SELECTION_CART_COLOR = "#FF414D";

/** Outline stroke used on catalog Lucide icons. */
export const CATALOG_ICON_STROKE = 2;

const CATEGORY_ICONS: Record<CategoryMark, LucideIcon> = {
  disk: HardDrive,
  power: BatteryCharging,
  rack: Server,
  cable: Cable,
  filter: Plug,
  router: Router,
  switch: Network,
  intercom: Phone,
  recorder: MonitorPlay,
  ptz: Video,
  audio: Volume2,
  access: KeyRound,
  bracket: Wrench,
  camera: Camera,
  neutral: Box,
};

/** Pure lookup used by tests and CategoryOutlineIcon. */
export function iconForCategoryMark(mark: CategoryMark): LucideIcon {
  return CATEGORY_ICONS[mark];
}

export function CategoryOutlineIcon({
  slug,
  className = "h-6 w-6",
}: {
  slug: string;
  className?: string;
}) {
  const Icon = iconForCategoryMark(categoryMark(slug));
  return <Icon aria-hidden="true" className={className} strokeWidth={CATALOG_ICON_STROKE} />;
}

type MetaIconProps = Pick<LucideProps, "className">;

const metaClass = "mt-0.5 h-3.5 w-3.5 shrink-0 text-mute";

export function ModelMetaIcon({ className = metaClass }: MetaIconProps) {
  return <Hash aria-hidden="true" className={className} strokeWidth={CATALOG_ICON_STROKE} />;
}

export function BrandMetaIcon({ className = metaClass }: MetaIconProps) {
  return <Building2 aria-hidden="true" className={className} strokeWidth={CATALOG_ICON_STROKE} />;
}

export function CategoryMetaIcon({ className = metaClass }: MetaIconProps) {
  return <Folder aria-hidden="true" className={className} strokeWidth={CATALOG_ICON_STROKE} />;
}

export function PriceMetaIcon({ className = "h-4 w-4 shrink-0 text-mute" }: MetaIconProps) {
  return <Tag aria-hidden="true" className={className} strokeWidth={CATALOG_ICON_STROKE} />;
}

export function ContactActionIcon({ className = "h-4 w-4 shrink-0" }: MetaIconProps) {
  return <Phone aria-hidden="true" className={className} strokeWidth={CATALOG_ICON_STROKE} />;
}

export function BackLinkIcon({ className = "h-4 w-4 shrink-0" }: MetaIconProps) {
  return <ChevronLeft aria-hidden="true" className={className} strokeWidth={CATALOG_ICON_STROKE} />;
}

export function SelectionCartIcon({
  className = "h-4 w-4 shrink-0",
  tone = "cart",
}: MetaIconProps & { tone?: "cart" | "inherit" }) {
  return (
    <ShoppingCart
      aria-hidden="true"
      className={className}
      color={tone === "cart" ? SELECTION_CART_COLOR : "currentColor"}
      strokeWidth={CATALOG_ICON_STROKE}
    />
  );
}
