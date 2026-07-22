export type Visibility = "public" | "private";

export interface Review {
  id: string;
  book_id: string;
  user_id: string;
  content: string;
  rating: number;
  tags: string[];
  visibility: Visibility;
  ai_summary: string | null;
  ai_feedback: string | null;
  ai_generated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewWithAuthor extends Review {
  author_name: string;
  like_count: number;
  liked_by_me: boolean;
}

export interface ReviewCreateInput {
  book_id: string;
  content: string;
  rating: number;
  tags: string[];
  visibility: Visibility;
}

export interface ReviewUpdateInput {
  content?: string;
  rating?: number;
  tags?: string[];
  visibility?: Visibility;
}
