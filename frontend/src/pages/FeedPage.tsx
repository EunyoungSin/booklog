import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { getFeed } from "../api/feed";
import { toggleLike } from "../api/likes";
import { extractErrorMessage } from "../api/errors";
import { useAuth } from "../contexts/AuthContext";
import { ReviewCard } from "../components/ReviewCard";
import type { FeedItem } from "../types/feed";

const PAGE_SIZE = 10;

export function FeedPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [items, setItems] = useState<FeedItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [tagInput, setTagInput] = useState("");
  const [activeTag, setActiveTag] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    // On a hard refresh, auth session restoration (refresh token exchange) is
    // still async when this page mounts. Fetching before it resolves sends the
    // request with no access token, so the backend treats it as anonymous and
    // every review comes back with liked_by_me: false — even ones this user
    // already liked. Wait for auth to settle so the response reflects the
    // real session.
    if (authLoading) return;
    setIsLoading(true);
    try {
      const data = await getFeed({ tag: activeTag, page, limit: PAGE_SIZE });
      setItems(data.items);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err, "피드를 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  }, [activeTag, page, authLoading]);

  useEffect(() => {
    void load();
  }, [load]);

  function handleTagSubmit(event: FormEvent) {
    event.preventDefault();
    setPage(1);
    setActiveTag(tagInput.trim() || undefined);
  }

  async function handleToggleLike(reviewId: string) {
    const result = await toggleLike(reviewId);
    setItems((prev) =>
      prev.map((item) =>
        item.id === reviewId
          ? { ...item, liked_by_me: result.liked, like_count: result.like_count }
          : item,
      ),
    );
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <h1>피드</h1>

      <div className="index-card">
        <p className="index-card-meta">FILTER CARD · TAG</p>
        <form className="form" style={{ flexDirection: "row", maxWidth: "none" }} onSubmit={handleTagSubmit}>
          <input
            style={{ flex: 1 }}
            placeholder="태그로 필터링 (예: 인생책)"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
          />
          <button className="btn btn-primary" type="submit">
            필터
          </button>
          {activeTag && (
            <button
              className="btn"
              type="button"
              onClick={() => {
                setTagInput("");
                setActiveTag(undefined);
                setPage(1);
              }}
            >
              초기화
            </button>
          )}
        </form>
      </div>

      {error && <p className="error-text">{error}</p>}
      {isLoading && <p className="page-status">불러오는 중...</p>}

      {!isLoading && items.length === 0 && (
        <p className="page-status">
          {activeTag ? `"${activeTag}" 태그의 공개 독후감이 없습니다.` : "아직 공개된 독후감이 없습니다."}
        </p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 24 }}>
        {items.map((item) => (
          <div key={item.id}>
            <Link
              to={`/books/${item.book.id}`}
              style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}
            >
              {item.book.cover_url && (
                <img src={item.book.cover_url} alt="" width={28} style={{ height: "auto", borderRadius: 2 }} />
              )}
              <strong style={{ color: "var(--text)", fontSize: 17 }}>{item.book.title}</strong>
            </Link>
            <ReviewCard
              review={item}
              isOwner={false}
              onToggleLike={user ? () => handleToggleLike(item.id) : undefined}
            />
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div style={{ display: "flex", gap: 8, marginTop: 20, justifyContent: "center" }}>
          <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            이전
          </button>
          <span className="muted" style={{ alignSelf: "center" }}>
            {page} / {totalPages}
          </span>
          <button className="btn" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            다음
          </button>
        </div>
      )}
    </div>
  );
}
