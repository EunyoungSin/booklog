import { useState, type FormEvent } from "react";
import { StarRatingInput } from "./StarRatingInput";
import { MarkdownContent } from "./MarkdownContent";
import type { Visibility } from "../types/review";

export interface ReviewFormValues {
  content: string;
  rating: number;
  tags: string[];
  visibility: Visibility;
}

export function ReviewForm({
  initialValues,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initialValues?: Partial<ReviewFormValues>;
  submitLabel: string;
  onSubmit: (values: ReviewFormValues) => Promise<void>;
  onCancel?: () => void;
}) {
  const [content, setContent] = useState(initialValues?.content ?? "");
  const [rating, setRating] = useState(initialValues?.rating ?? 5);
  const [tagsText, setTagsText] = useState((initialValues?.tags ?? []).join(", "));
  const [visibility, setVisibility] = useState<Visibility>(initialValues?.visibility ?? "public");
  const [showPreview, setShowPreview] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!content.trim()) return;

    const tags = tagsText
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    if (tags.length === 0) {
      setError("태그를 1개 이상 입력해주세요.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await onSubmit({ content, rating, tags, visibility });
    } catch {
      setError("저장에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form" style={{ maxWidth: "none" }} onSubmit={handleSubmit}>
      <label>
        별점
        <StarRatingInput value={rating} onChange={setRating} />
      </label>

      <label>
        내용 (마크다운 지원)
        <div className="tabs">
          <button type="button" className={!showPreview ? "active" : ""} onClick={() => setShowPreview(false)}>
            작성
          </button>
          <button type="button" className={showPreview ? "active" : ""} onClick={() => setShowPreview(true)}>
            미리보기
          </button>
        </div>
        {showPreview ? (
          <div className="card">
            <MarkdownContent content={content || "_내용을 입력하면 미리보기가 표시됩니다._"} />
          </div>
        ) : (
          <textarea
            rows={8}
            required
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
        )}
      </label>

      <label>
        태그 (쉼표로 구분, 1개 이상 필수)
        <input
          required
          value={tagsText}
          onChange={(e) => setTagsText(e.target.value)}
          placeholder="감동, 인생책"
        />
      </label>

      <label>
        공개 범위
        <select value={visibility} onChange={(e) => setVisibility(e.target.value as Visibility)}>
          <option value="public">공개</option>
          <option value="private">비공개</option>
        </select>
      </label>

      {error && <p className="error-text">{error}</p>}

      <div style={{ display: "flex", gap: 8 }}>
        <button className="btn btn-primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "저장 중..." : submitLabel}
        </button>
        {onCancel && (
          <button className="btn" type="button" onClick={onCancel}>
            취소
          </button>
        )}
      </div>
    </form>
  );
}
