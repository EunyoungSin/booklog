import { apiClient } from "./client";
import type { Page } from "../types/common";
import type { Quote, QuoteCreateInput, QuoteUpdateInput } from "../types/quote";

export async function createQuote(input: QuoteCreateInput): Promise<Quote> {
  const res = await apiClient.post<Quote>("/api/quotes", input);
  return res.data;
}

export async function listQuotesForBook(bookId: string): Promise<Page<Quote>> {
  const res = await apiClient.get<Page<Quote>>("/api/quotes", {
    params: { book_id: bookId, limit: 50 },
  });
  return res.data;
}

export async function updateQuote(quoteId: string, input: QuoteUpdateInput): Promise<Quote> {
  const res = await apiClient.put<Quote>(`/api/quotes/${quoteId}`, input);
  return res.data;
}

export async function deleteQuote(quoteId: string): Promise<void> {
  await apiClient.delete(`/api/quotes/${quoteId}`);
}
