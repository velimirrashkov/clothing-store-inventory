import { useEffect, useRef, useState } from "react";

import { useBarcodeLookup } from "../../api/inventory";
import type { VariantStaff } from "../../api/types";
import { useTranslation } from "../../i18n/LanguageContext";
import { formatMoney } from "../../lib/money";

/**
 * Native BarcodeDetector where the browser supports it (see architecture-spec.md §9 — "the
 * scanner view is just a back-office route using BarcodeDetector or zxing-js"), with a manual
 * text-entry fallback everywhere else so this never hard-depends on camera access or a specific
 * browser. No zxing-js dependency pulled in for Phase 1 — the fallback covers the gap.
 */
export function BarcodeLookup() {
  const { t } = useTranslation();
  const [barcode, setBarcode] = useState("");
  const [result, setResult] = useState<VariantStaff | null>(null);
  const [notFound, setNotFound] = useState(false);
  const lookup = useBarcodeLookup();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [scanning, setScanning] = useState(false);
  const [scannerSupported] = useState(() => "BarcodeDetector" in window);

  function runLookup(code: string) {
    if (!code) return;
    setNotFound(false);
    setResult(null);
    lookup.mutate(code, {
      onSuccess: (variant) => setResult(variant),
      onError: () => setNotFound(true),
    });
  }

  useEffect(() => {
    if (!scanning) return;
    let stream: MediaStream | null = null;
    let stop = false;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const Detector = (window as any).BarcodeDetector;
    const detector = new Detector({ formats: ["ean_13", "upc_a", "code_128"] });

    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } }).then((s) => {
      if (stop) {
        s.getTracks().forEach((t) => t.stop());
        return;
      }
      stream = s;
      if (videoRef.current) videoRef.current.srcObject = s;

      const tick = async () => {
        if (stop || !videoRef.current) return;
        try {
          const codes = await detector.detect(videoRef.current);
          if (codes[0]) {
            setBarcode(codes[0].rawValue);
            runLookup(codes[0].rawValue);
            setScanning(false);
            return;
          }
        } catch {
          // keep trying — a frame with no readable code isn't an error
        }
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });

    return () => {
      stop = true;
      stream?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanning]);

  return (
    <div className="space-y-3">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          runLookup(barcode);
        }}
        className="flex gap-2"
      >
        <input
          value={barcode}
          onChange={(e) => setBarcode(e.target.value)}
          placeholder={t("inventory.scan_or_type")}
          autoFocus
          className="flex-1 rounded border border-slate-300 px-3 py-2 text-sm"
        />
        <button type="submit" className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-700">
          {t("inventory.look_up")}
        </button>
        {scannerSupported && (
          <button
            type="button"
            onClick={() => setScanning((s) => !s)}
            className="rounded border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
          >
            {scanning ? t("inventory.stop_camera") : t("inventory.use_camera")}
          </button>
        )}
      </form>

      {scanning && (
        <video ref={videoRef} autoPlay muted playsInline className="w-full max-w-sm rounded border border-slate-300" />
      )}

      {notFound && <p className="text-sm text-red-600">{t("inventory.not_found")}</p>}

      {result && (
        <div className="rounded border border-slate-200 p-4 text-sm">
          <p className="font-semibold text-slate-900">{result.sku}</p>
          <p className="text-slate-600">
            {result.size} · {result.color} · {formatMoney(result.price_amount, result.currency)}
          </p>
          <p className={`mt-1 ${result.available <= 5 ? "font-semibold text-amber-700" : "text-slate-700"}`}>
            {t("inventory.available")}: {result.available}
          </p>
        </div>
      )}
    </div>
  );
}
