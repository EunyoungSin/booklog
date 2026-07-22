import { apiClient } from "./client";
import type { Page } from "../types/common";
import type { Comment } from "../types/comment";

export async function listComments(bookId: string): Promise<Page<Comment>> {
  const res = await apiClient.get<Page<Comment>>(`/api/books/${bookId}/comments`, {
    params: { limit: 100 },
  });
  return res.data;
}

export async function createComment(bookId: string, content: string): Promise<Comment> {
  const res = await apiClient.post<Comment>(`/api/books/${bookId}/comments`, { content });
  return res.data;
}

export async function deleteComment(commentId: string): Promise<void> {
  await apiClient.delete(`/api/comments/${commentId}`);
}
