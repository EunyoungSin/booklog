export interface MonthlyStats {
  year: number;
  month: number;
  books_added_count: number;
  reviews_written_count: number;
  average_rating: number | null;
}
