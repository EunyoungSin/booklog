export interface Quote {
  id: string;
  book_id: string;
  user_id: string;
  text: string;
  page: number | null;
  tags: string[];
  created_at: string;
}

export interface QuoteCreateInput {
  book_id: string;
  text: string;
  page?: number | null;
  tags: string[];
}

export interface QuoteUpdateInput {
  text?: string;
  page?: number | null;
  tags?: string[];
}
