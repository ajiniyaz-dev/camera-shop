import { showOriginalNote } from "@/lib/presentation";

export function ProductSpecTable({
  id,
  title,
  fallbackLabel,
  specifications,
}: {
  id?: string;
  title: string;
  fallbackLabel: string;
  specifications: Array<{ name: string; value: string; translation_fallback: boolean }>;
}) {
  const rows = specifications.filter((spec) => spec.name.trim() && spec.value.trim());
  if (!rows.length) {
    return null;
  }
  return (
    <section id={id} className="rounded-lg border border-line bg-white p-5 sm:p-6">
      <div aria-hidden="true" className="accent-rail" />
      <h2 className="mt-2 text-base font-semibold tracking-tight text-navy sm:text-lg">{title}</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[18rem] border-collapse text-left text-sm">
          <tbody>
            {rows.map((spec, index) => (
              <tr
                key={`${spec.name}-${index}`}
                className={`border-t border-line ${index % 2 === 1 ? "bg-mist/90" : "bg-white"}`}
              >
                <th scope="row" className="w-[38%] max-w-[16rem] px-3 py-2 align-top font-medium text-navy/70">
                  {spec.name}
                  {showOriginalNote(spec.translation_fallback, spec.name) ? (
                    <span className="mt-0.5 block text-xs font-normal text-mute">{fallbackLabel}</span>
                  ) : null}
                </th>
                <td className="px-3 py-2 align-top break-words text-ink/90">{spec.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
