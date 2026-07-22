import { apiClient } from "./client";
import type { Page } from "../types/common";
import type { FeedItem } from "../types/feed";

export async function getFeed(params: { tag?: string; page?: number; limit?: number }): Promise<Page<FeedItem>> {
  const res = await apiClient.get<Page<FeedItem>>("/api/feed", { params });
  return res.data;
}
