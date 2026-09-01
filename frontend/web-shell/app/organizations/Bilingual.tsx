import type { Bilingual as BilingualPair } from "./labels";

/**
 * Renders a German-authoritative / English-informational label pair.
 * German is the primary, unmarked text; English is a secondary,
 * explicitly `lang="en"` gloss in parentheses so assistive technology
 * announces the language switch correctly.
 */
export function Bilingual({ pair }: { pair: BilingualPair }) {
  return (
    <>
      {pair.de}{" "}
      <span lang="en" className="informational">
        ({pair.en})
      </span>
    </>
  );
}

export function formatDate(value: string | null): string {
  if (value === null) {
    return "—";
  }
  return new Date(value).toISOString().slice(0, 10);
}
