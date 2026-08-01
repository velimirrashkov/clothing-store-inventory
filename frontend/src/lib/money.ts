/** Amounts are always integer minor units server-side (see architecture-spec.md §4.1) — never a float. */
export function formatMoney(minorUnits: number, currency: string): string {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency }).format(minorUnits / 100);
}
