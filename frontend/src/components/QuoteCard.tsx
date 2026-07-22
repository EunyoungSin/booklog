import type { Quote } from "../types/quote";

export function QuoteCard({
  quote,
  onEdit,
  onDelete,
}: {
  quote: Quote;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
        <blockquote
          style={{
            margin: 0,
            paddingLeft: 12,
            borderLeft: "3px solid var(--brass)",
            color: "var(--text-h)",
          }}
        >
          “{quote.text}”
        </blockquote>
        <div style={{ display: "flex", gap: 8, flexShrink: 0, marginLeft: 12 }}>
          <button className="btn" onClick={onEdit}>
            수정
          </button>
          <button className="btn" onClick={onDelete}>
            삭제
          </button>
        </div>
      </div>
      <p className="muted" style={{ fontSize: 13, marginTop: 8 }}>
        {quote.page && `p. ${quote.page} · `}
        {new Date(quote.created_at).toLocaleDateString()}
      </p>
      {quote.tags.length > 0 && (
        <div>
          {quote.tags.map((tag) => (
            <span key={tag} className="tag">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
