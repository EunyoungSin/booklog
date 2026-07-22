import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getBook } from "../api/books";
import {
  createReview,
  deleteReview,
  listMyReviews,
  listPublicReviewsForBook,
  regenerateAiSummary,
  updateReview,
} from "../api/reviews";
import { createQuote, deleteQuote, listQuotesForBook, updateQuote } from "../api/quotes";
import { toggleLike } from "../api/likes";
import { extractErrorMessage } from "../api/errors";
import { useAuth } from "../contexts/AuthContext";
import { ReviewForm, type ReviewFormValues } from "../components/ReviewForm";
import { ReviewCard } from "../components/ReviewCard";
import { QuoteForm, type QuoteFormValues } from "../components/QuoteForm";
import { QuoteCard } from "../components/QuoteCard";
import { CommentThread } from "../components/CommentThread";
import { StampOverlay, useStamp } from "../components/StampOverlay";
import type { Book } from "../types/book";
import type { Review, ReviewWithAuthor } from "../types/review";
import type { Quote } from "../types/quote";

export function BookDetailPage() {
  const { bookId } = useParams<{ bookId: string }>();
  const { user } = useAuth();

  const [book, setBook] = useState<Book | null>(null);
  const [myReviews, setMyReviews] = useState<Review[]>([]);
  const [publicReviews, setPublicReviews] = useState<ReviewWithAuthor[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showReviewForm, setShowReviewForm] = useState(false);
  const [editingReviewId, setEditingReviewId] = useState<string | null>(null);
  const [showQuoteForm, setShowQuoteForm] = useState(false);
  const [editingQuoteId, setEditingQuoteId] = useState<string | null>(null);
  const [regeneratingReviewId, setRegeneratingReviewId] = useState<string | null>(null);
  const { triggerKey: stampKey, trigger: fireStamp } = useStamp();

  const loadAll = useCallback(async () => {
    if (!bookId) return;
    setIsLoading(true);
    try {
      const [bookData, publicReviewsPage] = await Promise.all([
        getBook(bookId),
        listPublicReviewsForBook(bookId),
      ]);
      setBook(bookData);
      setPublicReviews(publicReviewsPage.items);

      if (user) {
        const [myReviewsPage, quotesPage] = await Promise.all([
          listMyReviews(bookId),
          listQuotesForBook(bookId),
        ]);
        setMyReviews(myReviewsPage.items);
        setQuotes(quotesPage.items);
      } else {
        setMyReviews([]);
        setQuotes([]);
      }
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err, "책 정보를 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  }, [bookId, user]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  if (!bookId) return null;
  if (isLoading) return <p className="page-status">불러오는 중...</p>;
  if (error) return <p className="error-text">{error}</p>;
  if (!book) return null;

  async function handleCreateReview(values: ReviewFormValues) {
    await createReview({ book_id: bookId!, ...values });
    setShowReviewForm(false);
    await loadAll();
    fireStamp();
  }

  async function handleUpdateReview(reviewId: string, values: ReviewFormValues) {
    await updateReview(reviewId, values);
    setEditingReviewId(null);
    await loadAll();
    fireStamp();
  }

  async function handleDeleteReview(reviewId: string) {
    if (!confirm("이 독후감을 삭제할까요?")) return;
    await deleteReview(reviewId);
    await loadAll();
  }

  async function handleCreateQuote(values: QuoteFormValues) {
    await createQuote({ book_id: bookId!, ...values });
    setShowQuoteForm(false);
    await loadAll();
  }

  async function handleUpdateQuote(quoteId: string, values: QuoteFormValues) {
    await updateQuote(quoteId, values);
    setEditingQuoteId(null);
    await loadAll();
  }

  async function handleDeleteQuote(quoteId: string) {
    if (!confirm("이 인용문을 삭제할까요?")) return;
    await deleteQuote(quoteId);
    await loadAll();
  }

  async function handleRegenerateAi(reviewId: string) {
    setRegeneratingReviewId(reviewId);
    try {
      const updated = await regenerateAiSummary(reviewId);
      setMyReviews((prev) => prev.map((r) => (r.id === reviewId ? updated : r)));
    } catch (err) {
      setError(extractErrorMessage(err, "AI 요약/피드백 생성에 실패했습니다."));
    } finally {
      setRegeneratingReviewId(null);
    }
  }

  async function handleToggleLike(reviewId: string) {
    const result = await toggleLike(reviewId);
    setPublicReviews((prev) =>
      prev.map((r) =>
        r.id === reviewId ? { ...r, liked_by_me: result.liked, like_count: result.like_count } : r,
      ),
    );
  }

  const otherPublicReviews = publicReviews.filter((r) => r.user_id !== user?.id);

  return (
    <div>
      <StampOverlay triggerKey={stampKey} label="저장됨" />
      <div className="card" style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        {book.cover_url && (
          <img src={book.cover_url} alt="" width={100} style={{ height: "auto", borderRadius: 4 }} />
        )}
        <div>
          <h1 style={{ margin: 0 }}>{book.title}</h1>
          <p className="muted">{[book.author, book.publisher].filter(Boolean).join(" · ")}</p>
          {book.description && <p>{book.description}</p>}
        </div>
      </div>

      {user && (
        <section style={{ marginBottom: 32 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2>내 독후감</h2>
            {!showReviewForm && (
              <button className="btn btn-primary" onClick={() => setShowReviewForm(true)}>
                독후감 작성
              </button>
            )}
          </div>

          {showReviewForm && (
            <ReviewForm
              submitLabel="등록"
              onSubmit={handleCreateReview}
              onCancel={() => setShowReviewForm(false)}
            />
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 16 }}>
            {myReviews.map((review) =>
              editingReviewId === review.id ? (
                <ReviewForm
                  key={review.id}
                  initialValues={review}
                  submitLabel="수정 완료"
                  onSubmit={(values) => handleUpdateReview(review.id, values)}
                  onCancel={() => setEditingReviewId(null)}
                />
              ) : (
                <ReviewCard
                  key={review.id}
                  review={review}
                  isOwner
                  onEdit={() => setEditingReviewId(review.id)}
                  onDelete={() => handleDeleteReview(review.id)}
                  onRegenerateAi={() => handleRegenerateAi(review.id)}
                  isRegeneratingAi={regeneratingReviewId === review.id}
                />
              ),
            )}
            {myReviews.length === 0 && !showReviewForm && (
              <p style={{ color: "var(--text)" }}>아직 작성한 독후감이 없습니다.</p>
            )}
          </div>
        </section>
      )}

      <section style={{ marginBottom: 32 }}>
        <h2>다른 독자들의 독후감</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {otherPublicReviews.map((review) => (
            <ReviewCard
              key={review.id}
              review={review}
              isOwner={false}
              onToggleLike={user ? () => handleToggleLike(review.id) : undefined}
            />
          ))}
          {otherPublicReviews.length === 0 && (
            <p style={{ color: "var(--text)" }}>아직 공개된 독후감이 없습니다.</p>
          )}
        </div>
      </section>

      {!user && (
        <p className="muted" style={{ marginBottom: 32 }}>
          <Link to="/login">로그인</Link>하면 이 책에 대한 독후감과 인용문을 남길 수 있습니다.
        </p>
      )}

      {user && (
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>인용문</h2>
          {!showQuoteForm && (
            <button className="btn btn-primary" onClick={() => setShowQuoteForm(true)}>
              인용문 추가
            </button>
          )}
        </div>

        {showQuoteForm && (
          <QuoteForm
            submitLabel="등록"
            onSubmit={handleCreateQuote}
            onCancel={() => setShowQuoteForm(false)}
          />
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 16 }}>
          {quotes.map((quote) =>
            editingQuoteId === quote.id ? (
              <QuoteForm
                key={quote.id}
                initialValues={quote}
                submitLabel="수정 완료"
                onSubmit={(values) => handleUpdateQuote(quote.id, values)}
                onCancel={() => setEditingQuoteId(null)}
              />
            ) : (
              <QuoteCard
                key={quote.id}
                quote={quote}
                onEdit={() => setEditingQuoteId(quote.id)}
                onDelete={() => handleDeleteQuote(quote.id)}
              />
            ),
          )}
          {quotes.length === 0 && !showQuoteForm && (
            <p style={{ color: "var(--text)" }}>저장된 인용문이 없습니다.</p>
          )}
        </div>
      </section>
      )}

      <div style={{ marginTop: 32 }}>
        <CommentThread bookId={bookId} />
      </div>
    </div>
  );
}
