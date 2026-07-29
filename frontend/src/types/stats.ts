export interface MonthlyStats {
  year: number;
  month: number;
  books_added_count: number;
  reviews_written_count: number;
  average_rating: number | null;
}

/** 날짜 문자열(YYYY-MM-DD) -> 해당 날짜의 리뷰 개수 */
export type CalendarCounts = Record<string, number>;

export interface CalendarDayReview {
  id: string;
  book: {
    id: string;
    title: string;
  };
  rating: number;
  summary_preview: string;
  created_at: string;
}
