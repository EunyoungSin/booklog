import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { search } from "../api/search";
import { extractErrorMessage } from "../api/errors";
import type { SearchResultItem, SearchScope } from "../types/search";

const PAGE_SIZE = 20;

const SCOPE_LABELS: Record<SearchScope, string> = {
  all: "전체",
  books: "도서",
  reviews: "독후감",
  quotes: "인용문",
};

const TYPE_BADGE: Record<SearchResultItem["type"], string> = {
  book: "도서",
  review: "독후감",
  quote: "인용문",
};

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<SearchScope>("all");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<SearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(q: string, nextScope: SearchScope, nextPage: number) {
    if (!q.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await search(q.trim(), nextScope, nextPage, PAGE_SIZE);
      setItems(data.items);
      setTotal(data.total);
      setHasSearched(true);
    } catch (err) {
      setError(extractErrorMessage(err, "검색에 실패했습니다."));
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setPage(1);
    void runSearch(query, scope, 1);
  }

  function handleScopeChange(nextScope: SearchScope) {
    setScope(nextScope);
    setPage(1);
    if (hasSearched) void runSearch(query, nextScope, 1);
  }

  function handlePageChange(nextPage: number) {
    setPage(nextPage);
    void runSearch(query, scope, nextPage);
  }

  function resultLink(item: SearchResultItem): string | null {
    if (item.type === "book") return `/books/${item.id}`;
    if (item.book_id) return `/books/${item.book_id}`;
    return null;
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <h1>검색</h1>
      <p style={{ color: "var(--text)" }}>도서 제목, 태그, 독후감 본문, 인용문을 한 번에 검색합니다.</p>

      <div className="index-card">
        <p className="index-card-meta">CATALOG SEARCH</p>
        <form className="form" style={{ flexDirection: "row", maxWidth: "none" }} onSubmit={handleSubmit}>
          <input
            style={{ flex: 1 }}
            placeholder="검색어를 입력하세요"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn btn-primary" type="submit" disabled={isLoading}>
            {isLoading ? "검색 중..." : "검색"}
          </button>
        </form>

        <div className="tabs" style={{ marginBottom: 0, marginTop: 14 }}>
          {(Object.keys(SCOPE_LABELS) as SearchScope[]).map((s) => (
            <button
              key={s}
              className={scope === s ? "active" : ""}
              onClick={() => handleScopeChange(s)}
            >
              {SCOPE_LABELS[s]}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}

      {hasSearched && !isLoading && items.length === 0 && (
        <p className="page-status">검색 결과가 없습니다.</p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 20 }}>
        {items.map((item) => {
          const link = resultLink(item);
          const content = (
            <div className="card">
              <span className="tag">{TYPE_BADGE[item.type]}</span>
              <h3 style={{ margin: "8px 0 4px" }}>{item.title}</h3>
              {item.snippet && <p className="muted" style={{ margin: 0 }}>{item.snippet}</p>}
            </div>
          );
          return (
            <div key={`${item.type}-${item.id}`}>
              {link ? <Link to={link}>{content}</Link> : content}
            </div>
          );
        })}
      </div>

      {hasSearched && totalPages > 1 && (
        <div style={{ display: "flex", gap: 8, marginTop: 20, justifyContent: "center" }}>
          <button className="btn" disabled={page <= 1} onClick={() => handlePageChange(page - 1)}>
            이전
          </button>
          <span className="muted" style={{ alignSelf: "center" }}>
            {page} / {totalPages}
          </span>
          <button
            className="btn"
            disabled={page >= totalPages}
            onClick={() => handlePageChange(page + 1)}
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
}
