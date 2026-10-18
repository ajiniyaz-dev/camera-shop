export type CategoryMark =
  | "disk"
  | "power"
  | "rack"
  | "cable"
  | "filter"
  | "router"
  | "switch"
  | "intercom"
  | "recorder"
  | "ptz"
  | "audio"
  | "access"
  | "bracket"
  | "camera"
  | "neutral";

export function categoryMark(slug: string): CategoryMark {
  const value = slug.toLowerCase();
  if (value === "hdd") return "disk";
  if (value.includes("bespereboyn") || value.startsWith("bloki-pitaniya")) return "power";
  if (value.includes("shkaf")) return "rack";
  if (value.includes("kabel") || value.includes("razyom")) return "cable";
  if (value.includes("filtr")) return "filter";
  if (value.includes("marshrut")) return "router";
  if (value.includes("kommutator") || value.startsWith("poe-")) return "switch";
  if (value.includes("domofon")) return "intercom";
  if (value.startsWith("nvr") || value.startsWith("dvr") || value.includes("-dvr")) return "recorder";
  if (value.includes("ptz")) return "ptz";
  if (value.includes("zvuk")) return "audio";
  if (value === "skud") return "access";
  if (value.includes("montazh")) return "bracket";
  if (
    value.includes("kamer") ||
    value.startsWith("ik-") ||
    value.startsWith("colorvu") ||
    value.startsWith("turbo-hd") ||
    value.startsWith("wifi-") ||
    value.startsWith("hilook") ||
    value.startsWith("varifok") ||
    value.startsWith("ezviz")
  ) {
    return "camera";
  }
  return "neutral";
}
