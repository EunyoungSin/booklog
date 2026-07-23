export function pad(n: number): string {
  return String(n).padStart(2, "0");
}

/** local Y-M-D key, matching the `date` param the calendar stats endpoints expect */
export function dateKey(year: number, month: number, day: number): string {
  return `${year}-${pad(month)}-${pad(day)}`;
}
