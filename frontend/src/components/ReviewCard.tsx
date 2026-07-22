import { HeartIcon } from "./HeartIcon";
import { MarkdownContent } from "./MarkdownContent";
import type { Review, ReviewWithAuthor } from "../types/review";

function isReviewWithAuthor(review: Review | ReviewWithAuthor): review is ReviewWithAuthor {
  return "author_name" in review;
}

export function ReviewCard({
  review,
  isOwner,
  onEdit,
  onDelete,
  onToggleLike,
  onRegenerateAi,
  isRegeneratingAi,
}: {
  review: Review | ReviewWithAuthor;
  isOwner: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
  onToggleLike?: () => void;
  onRegenerateAi?: () => void;
  isRegeneratingAi?: boolean;
}) {
  const withAuthor = isReviewWithAuthor(review) ? review : null;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
        <div>
          {withAuthor && <strong style={{ marginRight: 8 }}>{withAuthor.author_name}</strong>}
          <span style={{ color: "var(--brass-strong)" }}>
            {"★".repeat(review.rating)}
            {"☆".repeat(5 - review.rating)}
          </span>
          {review.visibility === "private" && <span className="tag">비공개</span>}
        </div>
        {isOwner && (onEdit || onDelete) && (
          <div style={{ display: "flex", gap: 8 }}>
            {onEdit && (
              <button className="btn" onClick={onEdit}>
                수정
              </button>
            )}
            {onDelete && (
              <button className="btn" onClick={onDelete}>
                삭제
              </button>
            )}
          </div>
        )}
      </div>

      <div style={{ marginTop: 8 }}>
        <MarkdownContent content={review.content} />
      </div>

      {review.tags.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {review.tags.map((tag) => (
            <span key={tag} className="tag">
              {tag}
            </span>
          ))}
        </div>
      )}

      {review.ai_summary && (
        <div
          className="card"
          style={{ marginTop: 12, background: "var(--surface)", borderLeft: "3px solid var(--brass)" }}
        >
          <p className="muted" style={{ margin: "0 0 4px", fontSize: 13, fontWeight: 600 }}>
            🤖 AI 요약
          </p>
          <p style={{ margin: 0, color: "var(--text)" }}>{review.ai_summary}</p>
        </div>
      )}

      {isOwner && (review.ai_feedback || onRegenerateAi) && (
        <div
          className="card"
          style={{ marginTop: 8, background: "var(--surface)", borderLeft: "3px solid var(--burgundy)" }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
            <p className="muted" style={{ margin: "0 0 4px", fontSize: 13, fontWeight: 600 }}>
              ✍️ AI 글쓰기 피드백
            </p>
            {onRegenerateAi && (
              <button className="btn" onClick={onRegenerateAi} disabled={isRegeneratingAi}>
                {isRegeneratingAi ? "생성 중..." : "다시 생성"}
              </button>
            )}
          </div>
          <p style={{ margin: 0, color: "var(--text)" }}>
            {review.ai_feedback ?? (
              <span className="muted">아직 AI 피드백이 없습니다. 위 버튼으로 생성해보세요.</span>
            )}
          </p>
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>
          {new Date(review.created_at).toLocaleString()}
        </p>
        {withAuthor &&
          (onToggleLike ? (
            <button
              className="btn"
              onClick={onToggleLike}
              style={{ color: withAuthor.liked_by_me ? "var(--danger)" : "var(--text-h)" }}
            >
              <HeartIcon filled={withAuthor.liked_by_me} />
              {withAuthor.like_count}
            </button>
          ) : (
            <span className="btn" style={{ cursor: "default", color: "var(--text-h)" }}>
              <HeartIcon filled={withAuthor.liked_by_me} />
              {withAuthor.like_count}
            </span>
          ))}
      </div>
    </div>
  );
}
