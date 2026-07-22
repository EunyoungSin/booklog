import { apiClient } from "./client";
import type { Page } from "../types/common";
import type { Book, BookSearchResult, LibraryItem } from "../types/book";

export async function searchBooks(query: string): Promise<BookSearchResult[]> {
  const res = await apiClient.get<BookSearchResult[]>("/api/books/search", {
    params: { query },
  });
  return res.data;
}

export interface BookRegisterInput {
  title: string;
  author?: string | null;
  isbn?: string | null;
  cover_url?: string | null;
  publisher?: string | null;
  description?: string | null;
}

export async function registerBook(input: BookRegisterInput): Promise<Book> {
  const res = await apiClient.post<Book>("/api/books", input);
  return res.data;
}

export async function getMyLibrary(page = 1, limit = 20): Promise<Page<LibraryItem>> {
  const res = await apiClient.get<Page<LibraryItem>>("/api/library/me", {
    params: { page, limit },
  });
  return res.data;
}

export async function getBook(bookId: string): Promise<Book> {
  const res = await apiClient.get<Book>(`/api/books/${bookId}`);
  return res.data;
}

export async function removeFromLibrary(bookId: string): Promise<void> {
  await apiClient.delete(`/api/library/${bookId}`);
}
