import { useState, type FormEvent } from "react";
import type { BookRegisterInput } from "../api/books";

export function ManualBookForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (input: BookRegisterInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [isbn, setIsbn] = useState("");
  const [publisher, setPublisher] = useState("");
  const [coverUrl, setCoverUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        title: title.trim(),
        author: author.trim() || null,
        isbn: isbn.trim() || null,
        publisher: publisher.trim() || null,
        cover_url: coverUrl.trim() || null,
      });
    } catch {
      setError("등록에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label>
        제목 *
        <input required value={title} onChange={(e) => setTitle(e.target.value)} />
      </label>
      <label>
        저자
        <input value={author} onChange={(e) => setAuthor(e.target.value)} />
      </label>
      <label>
        출판사
        <input value={publisher} onChange={(e) => setPublisher(e.target.value)} />
      </label>
      <label>
        ISBN (선택)
        <input value={isbn} onChange={(e) => setIsbn(e.target.value)} />
      </label>
      <label>
        표지 이미지 URL (선택)
        <input value={coverUrl} onChange={(e) => setCoverUrl(e.target.value)} />
      </label>
      {error && <p className="error-text">{error}</p>}
      <div style={{ display: "flex", gap: 8 }}>
        <button className="btn btn-primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "등록 중..." : "서재에 등록"}
        </button>
        <button className="btn" type="button" onClick={onCancel}>
          취소
        </button>
      </div>
    </form>
  );
}
