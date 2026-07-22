export function StarRatingInput({
  value,
  onChange,
}: {
  value: number;
  onChange: (rating: number) => void;
}) {
  return (
    <div role="radiogroup" aria-label="별점" style={{ display: "flex", gap: 4 }}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star}점`}
          onClick={() => onChange(star)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: 22,
            padding: 0,
            lineHeight: 1,
            color: star <= value ? "var(--brass-strong)" : "var(--border)",
          }}
        >
          ★
        </button>
      ))}
    </div>
  );
}
