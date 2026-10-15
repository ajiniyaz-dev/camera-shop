"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { focusDark } from "@/components/public/brand-mark";

export function SiteNav({
  links,
  label,
}: {
  links: Array<{ href: string; label: string }>;
  label: string;
}) {
  const pathname = usePathname() || "/";
  return (
    <nav aria-label={label} className="flex flex-col md:flex-row md:items-center md:gap-1">
      {links.map((link) => {
        const current =
          pathname === link.href ||
          (link.href !== "/" && pathname.startsWith(`${link.href}/`) && link.href.split("/").length > 2);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={current ? "page" : undefined}
            className={`inline-flex min-h-11 items-center border-l-2 px-3 text-sm md:border-b-2 md:border-l-0 ${focusDark} ${
              current
                ? "border-teal text-white"
                : "border-transparent text-white/75 hover:text-white"
            }`}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
