export interface BookSearchResult {
  title: string;
  author: string | null;
  isbn: string | null;
  cover_url: string | null;
  publisher: string | null;
  description: string | null;
  pub_date: string | null;
}

export interface Book {
  id: string;
  title: string;
  author: string | null;
  isbn: string | null;
  cover_url: string | null;
  publisher: string | null;
  description: string | null;
  added_by: string;
  created_at: string;
}

export interface LibraryItem {
  book: Book;
  added_at: string;
}
