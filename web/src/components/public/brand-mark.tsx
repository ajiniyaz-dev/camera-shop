export const focusDark =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal";

export const focusLight =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

export function BrandMark() {
  return (
    <span aria-hidden="true" className="relative inline-block h-7 w-7 shrink-0 bg-brand">
      <span className="absolute bottom-0 right-0 h-2.5 w-2.5 bg-teal" />
    </span>
  );
}

export function AccentBar() {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_4.5rem]" aria-hidden="true">
      <div className="h-1 bg-brand" />
      <div className="h-1 bg-teal" />
    </div>
  );
}

export function FolderGlyph({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path className="fill-current" d="M3 6.5h6.2l1.6 2.2H21V19H3V6.5Z" />
      <path className="fill-teal" d="M3 11h18v1.6H3z" />
    </svg>
  );
}

export function CameraGlyph({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect x="2" y="9" width="3" height="14" className="fill-current" />
      <rect x="5" y="14" width="6" height="2" className="fill-current" />
      <rect x="11" y="10" width="17" height="8" className="fill-current" />
      <rect x="13" y="8" width="13" height="2" className="fill-teal" />
      <circle cx="25" cy="14" r="3.1" className="fill-mist" />
      <circle cx="25" cy="14" r="1.35" className="fill-teal" />
    </svg>
  );
}

export function CameraFigure() {
  return (
    <svg viewBox="0 0 168 120" className="h-auto max-h-32 w-full" aria-hidden="true">
      <rect x="8" y="14" width="6" height="92" className="fill-navy" />
      <rect x="14" y="48" width="28" height="6" className="fill-brand" />
      <rect x="40" y="28" width="104" height="40" className="fill-navy" />
      <rect x="50" y="18" width="84" height="10" className="fill-brand" />
      <circle cx="124" cy="48" r="18" className="fill-mist" />
      <circle cx="124" cy="48" r="10" className="fill-brand" />
      <circle cx="124" cy="48" r="4" className="fill-teal" />
      <rect x="62" y="68" width="5" height="24" className="fill-brand" />
      <rect x="52" y="90" width="25" height="5" className="fill-navy" />
    </svg>
  );
}
