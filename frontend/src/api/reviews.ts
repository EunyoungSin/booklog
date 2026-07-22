import { apiClient } from "./client";
import type { Page } from "../types/common";
import type {
  Review,
  ReviewCreateInput,
  ReviewUpdateInput,
  ReviewWithAuthor,
} from "../types/review";

export async function createReview(input: ReviewCreateInput): Promise<Review> {
  const res = await apiClient.post<Review>("/api/reviews", input);
  return res.data;
}

export async function listMyReviews(bookId: string): Promise<Page<Review>> {
  const res = await apiClient.get<Page<Review>>("/api/reviews", {
    params: { book_id: bookId, mine: true, limit: 50 },
  });
  return res.data;
}

export async function updateReview(reviewId: string, input: ReviewUpdateInput): Promise<Review> {
  const res = await apiClient.put<Review>(`/api/reviews/${reviewId}`, input);
  return res.data;
}

export async function deleteReview(reviewId: string): Promise<void> {
  await apiClient.delete(`/api/reviews/${reviewId}`);
}

export async function regenerateAiSummary(reviewId: string): Promise<Review> {
  const res = await apiClient.post<Review>(`/api/reviews/${reviewId}/ai-regenerate`);
  return res.data;
}

export async function listPublicReviewsForBook(
  bookId: string,
  page = 1,
  limit = 20,
): Promise<Page<ReviewWithAuthor>> {
  const res = await apiClient.get<Page<ReviewWithAuthor>>(`/api/books/${bookId}/reviews`, {
    params: { page, limit },
  });
  return res.data;
}
