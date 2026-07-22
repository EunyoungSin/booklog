export type SearchResultType = "book" | "review" | "quote";
export type SearchScope = "all" | "books" | "reviews" | "quotes";

export interface SearchResultItem {
  type: SearchResultType;
  id: string;
  book_id: string | null;
  title: string;
  snippet: string | null;
}
