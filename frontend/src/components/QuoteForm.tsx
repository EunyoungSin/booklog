import { useState, type FormEvent } from "react";

export interface QuoteFormValues {
  text: string;
  page: number | null;
  tags: string[];
}

export function QuoteForm({
  initialValues,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initialValues?: Partial<QuoteFormValues>;
  submitLabel: string;
  onSubmit: (values: QuoteFormValues) => Promise<void>;
  onCancel?: () => void;
}) {
  const [text, setText] = useState(initialValues?.text ?? "");
  const [page, setPage] = useState(initialValues?.page?.toString() ?? "");
  const [tagsText, setTagsText] = useState((initialValues?.tags ?? []).join(", "));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;

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
      await onSubmit({ text, page: page.trim() ? Number(page) : null, tags });
    } catch {
      setError("저장에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label>
        인용문
        <textarea rows={3} required value={text} onChange={(e) => setText(e.target.value)} />
      </label>
      <label>
        페이지 (선택)
        <input
          type="number"
          min={1}
          value={page}
          onChange={(e) => setPage(e.target.value)}
        />
      </label>
      <label>
        태그 (쉼표로 구분)
        <input value={tagsText} onChange={(e) => setTagsText(e.target.value)} placeholder="명언" />
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
