"use client";

import { useEffect, useState, type MouseEvent } from "react";

export type Locale = "de" | "en";

export function localeFrom(value: string | null | undefined): Locale {
  return value === "en" ? "en" : "de";
}

export function LanguageSelector() {
  const [locale, setLocale] = useState<Locale>("de");

  useEffect(() => {
    const current = localeFrom(
      new URLSearchParams(window.location.search).get("lang"),
    );
    setLocale(current);
    document.documentElement.lang = current;
  }, []);

  function select(nextLocale: Locale, event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    const query = nextLocale === "en" ? "?lang=en" : "";
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${query}`,
    );
    setLocale(nextLocale);
    document.documentElement.lang = nextLocale;
    window.dispatchEvent(new PopStateEvent("popstate"));
  }

  return (
    <div
      aria-label="Sprache / language"
      className="language-selector"
      data-locale={locale}
      role="group"
    >
      <a
        aria-current={locale === "de" ? "true" : undefined}
        href="?lang=de"
        onClick={(event) => select("de", event)}
      >
        DE
      </a>
      <span aria-hidden="true">|</span>
      <a
        aria-current={locale === "en" ? "true" : undefined}
        href="?lang=en"
        onClick={(event) => select("en", event)}
      >
        EN
      </a>
    </div>
  );
}
