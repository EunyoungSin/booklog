import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { registerBook, searchBooks, type BookRegisterInput } from "../api/books";
import { extractErrorMessage } from "../api/errors";
import { useAuth } from "../contexts/AuthContext";
import { ManualBookForm } from "../components/ManualBookForm";
import type { BookSearchResult } from "../types/book";

export function BookSearchPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<BookSearchResult[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [registeredIsbns, setRegisteredIsbns] = useState<Set<string>>(new Set());
  const [registeringIsbn, setRegisteringIsbn] = useState<string | null>(null);
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualRegistered, setManualRegistered] = useState(false);

  async function handleSearch(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    setError(null);
    try {
      setResults(await searchBooks(query.trim()));
    } catch (err) {
      setError(extractErrorMessage(err, "도서 검색에 실패했습니다."));
      setResults(null);
    } finally {
      setIsSearching(false);
    }
  }

  async function handleRegister(book: BookSearchResult) {
    const key = book.isbn ?? book.title;
    setRegisteringIsbn(key);
    setError(null);
    try {
      await registerBook({
        title: book.title,
        author: book.author,
        isbn: book.isbn,
        cover_url: book.cover_url,
        publisher: book.publisher,
        description: book.description,
      });
      setRegisteredIsbns((prev) => new Set(prev).add(key));
    } catch (err) {
      setError(extractErrorMessage(err, "서재 등록에 실패했습니다."));
    } finally {
      setRegisteringIsbn(null);
    }
  }

  async function handleManualRegister(input: BookRegisterInput) {
    await registerBook(input);
    setManualRegistered(true);
    setShowManualForm(false);
  }

  return (
    <div>
      <h1>도서 등록</h1>
      <div className="index-card">
        <p className="index-card-meta">ACQUISITION SLIP · TITLE / AUTHOR</p>
        <form className="form" style={{ flexDirection: "row", maxWidth: "none" }} onSubmit={handleSearch}>
          <input
            style={{ flex: 1 }}
            placeholder="책 제목, 저자로 검색"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn btn-primary" type="submit" disabled={isSearching}>
            {isSearching ? "검색 중..." : "검색"}
          </button>
        </form>
      </div>

      {user ? (
        <>
          <p className="muted" style={{ marginTop: 12 }}>
            검색 결과에 없는 책은{" "}
            {!showManualForm && (
              <button
                className="btn"
                style={{ padding: "2px 10px" }}
                onClick={() => setShowManualForm(true)}
              >
                직접 입력해서 등록
              </button>
            )}
            {showManualForm && "할 수 있습니다."}
          </p>

          {showManualForm && (
            <ManualBookForm
              onSubmit={handleManualRegister}
              onCancel={() => setShowManualForm(false)}
            />
          )}

          {manualRegistered && (
            <p className="muted" style={{ marginTop: 8 }}>
              등록되었습니다. <Link to="/library">내 서재에서 확인하기 →</Link>
            </p>
          )}
        </>
      ) : (
        <p className="muted" style={{ marginTop: 12 }}>
          <Link to="/login">로그인</Link>하면 검색한 책을 내 서재에 등록할 수 있습니다.
        </p>
      )}

      {error && (
        <p className="error-text" style={{ marginTop: 12 }}>
          {error}
        </p>
      )}

      {results !== null && results.length === 0 && !isSearching && (
        <p className="page-status">검색 결과가 없습니다.</p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 20 }}>
        {results?.map((book) => {
          const key = book.isbn ?? book.title;
          const isRegistered = registeredIsbns.has(key);
          return (
            <div key={key} className="card" style={{ display: "flex", gap: 12 }}>
              {book.cover_url && (
                <img
                  src={book.cover_url}
                  alt=""
                  width={64}
                  style={{ height: "auto", borderRadius: 4, alignSelf: "start" }}
                />
              )}
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: 0 }}>{book.title}</h3>
                <p className="muted" style={{ margin: "4px 0" }}>
                  {[book.author, book.publisher].filter(Boolean).join(" · ")}
                </p>
              </div>
              {user ? (
                <button
                  className="btn"
                  disabled={isRegistered || registeringIsbn === key}
                  onClick={() => handleRegister(book)}
                >
                  {isRegistered ? "등록됨" : registeringIsbn === key ? "등록 중..." : "서재에 등록"}
                </button>
              ) : (
                <Link to="/login" className="btn">
                  로그인 후 등록
                </Link>
              )}
            </div>
          );
        })}
      </div>

      {registeredIsbns.size > 0 && (
        <p className="muted" style={{ marginTop: 16 }}>
          <Link to="/library">내 서재에서 확인하기 →</Link>
        </p>
      )}
    </div>
  );
}
