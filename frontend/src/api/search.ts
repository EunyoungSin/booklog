import { apiClient } from "./client";
import type { Page } from "../types/common";
import type { SearchResultItem, SearchScope } from "../types/search";

export async function search(
  q: string,
  type: SearchScope,
  page = 1,
  limit = 20,
): Promise<Page<SearchResultItem>> {
  const res = await apiClient.get<Page<SearchResultItem>>("/api/search", {
    params: { q, type, page, limit },
  });
  return res.data;
}
