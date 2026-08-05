import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

import { translations } from "./translations";
import type { Locale } from "./translations";

const STORAGE_KEY = "backoffice-lang";

interface LanguageContextValue {
  lang: Locale;
  setLang: (lang: Locale) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

function readStoredLang(): Locale {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "en" ? "en" : "bg"; // BG default — Bulgarian-market business
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Locale>(readStoredLang);

  function setLang(next: Locale) {
    setLangState(next);
    localStorage.setItem(STORAGE_KEY, next);
  }

  function t(key: string): string {
    const entry = translations[key];
    if (!entry) {
      console.warn(`Missing translation key: "${key}"`);
      return key;
    }
    return entry[lang];
  }

  return <LanguageContext.Provider value={{ lang, setLang, t }}>{children}</LanguageContext.Provider>;
}

export function useTranslation() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useTranslation must be used within a LanguageProvider");
  return ctx;
}
