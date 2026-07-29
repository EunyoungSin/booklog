export function pad(n: number): string {
  return String(n).padStart(2, "0");
}

/** 캘린더 통계 엔드포인트가 기대하는 `date` 파라미터 형식과 일치하는 로컬 Y-M-D 키 */
export function dateKey(year: number, month: number, day: number): string {
  return `${year}-${pad(month)}-${pad(day)}`;
}
