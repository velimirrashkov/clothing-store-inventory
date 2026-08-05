import { useTranslation } from "./LanguageContext";

export function LanguageSwitcher() {
  const { lang, setLang } = useTranslation();

  return (
    <div className="flex gap-1 text-xs">
      {(["bg", "en"] as const).map((code) => (
        <button
          key={code}
          onClick={() => setLang(code)}
          className={`rounded px-1.5 py-0.5 uppercase ${
            lang === code ? "bg-slate-900 text-white" : "text-slate-500 hover:bg-slate-200"
          }`}
        >
          {code}
        </button>
      ))}
    </div>
  );
}
