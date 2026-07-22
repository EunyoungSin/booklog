import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { createComment, deleteComment, listComments } from "../api/comments";
import { extractErrorMessage } from "../api/errors";
import { useAuth } from "../contexts/AuthContext";
import type { Comment } from "../types/comment";

export function CommentThread({ bookId }: { bookId: string }) {
  const { user } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [text, setText] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const page = await listComments(bookId);
      setComments(page.items);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err, "댓글을 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  }, [bookId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    try {
      await createComment(bookId, text.trim());
      setText("");
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "댓글 작성에 실패했습니다."));
    }
  }

  async function handleDelete(commentId: string) {
    if (!confirm("댓글을 삭제할까요?")) return;
    try {
      await deleteComment(commentId);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "댓글 삭제에 실패했습니다."));
    }
  }

  return (
    <section>
      <h2>댓글</h2>
      {user ? (
        <form
          className="form"
          style={{ flexDirection: "row", maxWidth: "none" }}
          onSubmit={handleSubmit}
        >
          <input
            style={{ flex: 1 }}
            placeholder="댓글을 남겨보세요"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <button className="btn btn-primary" type="submit">
            등록
          </button>
        </form>
      ) : (
        <p className="muted">
          <Link to="/login">로그인</Link>하면 댓글을 남길 수 있습니다.
        </p>
      )}

      {error && <p className="error-text">{error}</p>}

      {isLoading ? (
        <p className="page-status">불러오는 중...</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
          {comments.map((comment) => (
            <div key={comment.id} className="card" style={{ display: "flex", justifyContent: "space-between" }}>
              <div>
                <strong>{comment.author_name}</strong>
                <p style={{ margin: "4px 0" }}>{comment.content}</p>
                <p className="muted" style={{ fontSize: 13, margin: 0 }}>
                  {new Date(comment.created_at).toLocaleString()}
                </p>
              </div>
              {user?.id === comment.user_id && (
                <button className="btn" onClick={() => handleDelete(comment.id)}>
                  삭제
                </button>
              )}
            </div>
          ))}
          {comments.length === 0 && <p style={{ color: "var(--text)" }}>아직 댓글이 없습니다.</p>}
        </div>
      )}
    </section>
  );
}
