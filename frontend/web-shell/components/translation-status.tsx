"use client";

import { useEffect, useState } from "react";

export function TranslationStatusNotice() {
  const [english, setEnglish] = useState(false);
  useEffect(() => {
    const sync = () =>
      setEnglish(new URLSearchParams(window.location.search).get("lang") === "en");
    sync();
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  if (!english) return null;
  return (
    <aside
      className="public-note"
      data-translation-state="fallback"
      lang="en"
      role="status"
    >
      <strong>English rendition status:</strong> No approved English translation is
      available for this material in this candidate. The current German source
      remains authoritative and visible; no stale English text is presented as
      current authority.
    </aside>
  );
}
