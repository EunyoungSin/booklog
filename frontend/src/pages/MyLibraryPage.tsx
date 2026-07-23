import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyLibrary, removeFromLibrary } from "../api/books";
import { extractErrorMessage } from "../api/errors";
import { useAuth } from "../contexts/AuthContext";
import type { LibraryItem } from "../types/book";

const PAGE_SIZE = 20;

export function MyLibraryPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setIsLoading(false);
      return;
    }
    let cancelled = false;
    setIsLoading(true);
    getMyLibrary(page, PAGE_SIZE)
      .then((data) => {
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
        setError(null);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "서재를 불러오지 못했습니다."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, user]);

  async function handleRemove(bookId: string) {
    try {
      await removeFromLibrary(bookId);
      setItems((prev) => prev.filter((item) => item.book.id !== bookId));
      setTotal((prev) => prev - 1);
    } catch (err) {
      setError(extractErrorMessage(err, "서재에서 제거하지 못했습니다."));
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <h1>내 서재</h1>

      {!user && (
        <p className="muted" style={{ marginTop: 12 }}>
          <Link to="/login">로그인</Link>하면 내 서재를 볼 수 있습니다.
        </p>
      )}

      {user && error && <p className="error-text">{error}</p>}

      {user && isLoading && <p className="page-status">불러오는 중...</p>}

      {user && !isLoading && items.length === 0 && (
        <p className="page-status">
          서재에 등록된 책이 없습니다. <Link to="/books/search">도서를 검색해 등록해보세요.</Link>
        </p>
      )}

      {user && (
        <div className="shelf">
          {items.map(({ book, added_at }) => (
            <div key={book.id} className="shelf-book">
              <Link to={`/books/${book.id}`} aria-label={book.title}>
                {book.cover_url ? (
                  <img src={book.cover_url} alt="" className="shelf-book-cover" />
                ) : (
                  <div className="shelf-book-cover no-image">{book.title}</div>
                )}
              </Link>
              <p className="shelf-book-title">
                <Link to={`/books/${book.id}`}>{book.title}</Link>
              </p>
              <p className="muted" style={{ fontSize: 12, margin: "2px 0 6px" }}>
                {new Date(added_at).toLocaleDateString()} 등록
              </p>
              <button
                className="btn"
                style={{ fontSize: 12, padding: "3px 10px" }}
                onClick={() => handleRemove(book.id)}
              >
                제거
              </button>
            </div>
          ))}
        </div>
      )}

      {user && totalPages > 1 && (
        <div style={{ display: "flex", gap: 8, marginTop: 20, justifyContent: "center" }}>
          <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            이전
          </button>
          <span className="muted" style={{ alignSelf: "center" }}>
            {page} / {totalPages}
          </span>
          <button
            className="btn"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
}
