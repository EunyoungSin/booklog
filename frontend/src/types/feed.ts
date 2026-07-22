import type { ReviewWithAuthor } from "./review";

export interface FeedBookInfo {
  id: string;
  title: string;
  cover_url: string | null;
}

export interface FeedItem extends ReviewWithAuthor {
  book: FeedBookInfo;
}
