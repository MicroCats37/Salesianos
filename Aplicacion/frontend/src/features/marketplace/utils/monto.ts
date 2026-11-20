/**
 * The money of a commercial view.
 *
 * The amount arrives as a NUMBER because the target presenters type it as
 * `Decimal` and the target serialises it as a float
 * (`Aplicacion/backend/core/types.py` → `BaseSchema.ser_json_decimal_to_float`).
 *
 * The browser never computes an amount: it prints the one the server sent.
 * The only thing this helper does is SHOW it with the two decimals of the
 * currency, without a locale (a locale would make the server and the browser
 * disagree about the same number).
 */
export function formatearMonto(monto: number, moneda: string): string {
  if (moneda.length === 0) return monto.toFixed(2);
  return `${moneda} ${monto.toFixed(2)}`;
}
