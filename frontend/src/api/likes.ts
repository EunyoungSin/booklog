import { apiClient } from "./client";

export interface LikeToggleResponse {
  liked: boolean;
  like_count: number;
}

export async function toggleLike(reviewId: string): Promise<LikeToggleResponse> {
  const res = await apiClient.post<LikeToggleResponse>(`/api/reviews/${reviewId}/like`);
  return res.data;
}
