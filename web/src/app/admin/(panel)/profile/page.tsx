"use client";

import { useEffect, useState } from "react";

import { useAdminLocale } from "@/components/admin/shell";
import { adminJson, ApiError } from "@/lib/admin-api";
import { translate } from "@/lib/i18n";

type LinkRow = { label: string; url: string };
type Profile = {
  public_name: string;
  legal_name: string | null;
  domain: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  opening_hours: string | null;
  social_links: LinkRow[];
};

const field = "mt-1 w-full rounded border border-neutral-300 px-3 py-2";

export default function ProfilePage() {
  const locale = useAdminLocale();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    adminJson<Profile>("/api/admin/profile").then(setProfile).catch(() => setMessage(translate(locale, "error")));
  }, [locale]);

  if (!profile) {
    return <p>{message || translate(locale, "loading")}</p>;
  }

  const loaded = profile;

  function set<K extends keyof Profile>(key: K, value: Profile[K]) {
    setProfile({ ...profile!, [key]: value });
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const saved = await adminJson<Profile>(
        "/api/admin/profile",
        { method: "PATCH" },
        {
          ...loaded,
          social_links: loaded.social_links.filter((link) => link.label.trim() && link.url.trim()),
        },
      );
      setProfile(saved);
      setMessage(translate(locale, "saved"));
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : translate(locale, "error"));
    }
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold">{translate(locale, "profile")}</h1>
      <form onSubmit={save} className="mt-4 grid gap-3 sm:grid-cols-2">
        <Text label={translate(locale, "name")} value={profile.public_name} onChange={(value) => set("public_name", value)} required />
        <Text label={translate(locale, "legalName")} value={profile.legal_name ?? ""} onChange={(value) => set("legal_name", value)} />
        <Text label={translate(locale, "domain")} value={profile.domain ?? ""} onChange={(value) => set("domain", value)} />
        <Text label={translate(locale, "phone")} value={profile.phone ?? ""} onChange={(value) => set("phone", value)} />
        <Text label={translate(locale, "email")} value={profile.email ?? ""} onChange={(value) => set("email", value)} />
        <Text label={translate(locale, "address")} value={profile.address ?? ""} onChange={(value) => set("address", value)} />
        <Text label={translate(locale, "hours")} value={profile.opening_hours ?? ""} onChange={(value) => set("opening_hours", value)} />
        <div className="sm:col-span-2">
          <h2 className="text-sm font-medium">{translate(locale, "addLink")}</h2>
          {profile.social_links.map((link, index) => (
            <div key={index} className="mt-2 grid gap-2 sm:grid-cols-2">
              <input aria-label={translate(locale, "socialLabel")} value={link.label} onChange={(event) => replaceLink(index, { ...link, label: event.target.value })} className={field} />
              <input aria-label={translate(locale, "socialUrl")} value={link.url} onChange={(event) => replaceLink(index, { ...link, url: event.target.value })} className={field} />
            </div>
          ))}
          <button type="button" className="mt-2 text-sm underline" onClick={() => set("social_links", [...profile.social_links, { label: "", url: "" }])}>
            {translate(locale, "addLink")}
          </button>
        </div>
        {message ? <p className="text-sm sm:col-span-2">{message}</p> : null}
        <button type="submit" className="w-fit rounded bg-neutral-900 px-4 py-2 text-sm text-white">
          {translate(locale, "save")}
        </button>
      </form>
    </section>
  );

  function replaceLink(index: number, link: LinkRow) {
    set(
      "social_links",
      profile!.social_links.map((item, itemIndex) => (itemIndex === index ? link : item)),
    );
  }
}

function Text({ label, value, onChange, required = false }: { label: string; value: string; onChange: (value: string) => void; required?: boolean }) {
  return (
    <label className="block text-sm">
      {label}
      <input required={required} value={value} onChange={(event) => onChange(event.target.value)} className={field} />
    </label>
  );
}
