export interface MonthlyStats {
  year: number;
  month: number;
  books_added_count: number;
  reviews_written_count: number;
  average_rating: number | null;
}

/** date string (YYYY-MM-DD) -> review count on that day */
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
