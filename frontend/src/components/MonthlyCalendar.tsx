import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCalendarDay, getCalendarMonth } from "../api/stats";
import { extractErrorMessage } from "../api/errors";
import { dateKey } from "../utils/date";
import type { CalendarCounts, CalendarDayReview } from "../types/stats";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

export function MonthlyCalendar() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [counts, setCounts] = useState<CalendarCounts>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [dayReviews, setDayReviews] = useState<CalendarDayReview[]>([]);
  const [isDayLoading, setIsDayLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setSelectedDate(null);
    setDayReviews([]);
    getCalendarMonth(year, month)
      .then((data) => {
        if (cancelled) return;
        setCounts(data);
        setError(null);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "캘린더를 불러오지 못했습니다."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [year, month]);

  function goToPrevMonth() {
    if (month === 1) {
      setYear((y) => y - 1);
      setMonth(12);
    } else {
      setMonth((m) => m - 1);
    }
  }

  function goToNextMonth() {
    if (month === 12) {
      setYear((y) => y + 1);
      setMonth(1);
    } else {
      setMonth((m) => m + 1);
    }
  }

  function handleSelectDay(key: string) {
    setSelectedDate(key);
    setIsDayLoading(true);
    getCalendarDay(key)
      .then((data) => {
        setDayReviews(data);
        setError(null);
      })
      .catch((err) => setError(extractErrorMessage(err, "독후감 목록을 불러오지 못했습니다.")))
      .finally(() => setIsDayLoading(false));
  }

  const firstWeekday = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const todayKey = dateKey(today.getFullYear(), today.getMonth() + 1, today.getDate());

  const cells: (number | null)[] = [
    ...Array(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  return (
    <section className="card">
      <div className="calendar-header">
        <button className="btn" onClick={goToPrevMonth} aria-label="이전 달">
          ◀
        </button>
        <h3 style={{ margin: 0 }}>
          {year}년 {month}월
        </h3>
        <button className="btn" onClick={goToNextMonth} aria-label="다음 달">
          ▶
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      {isLoading ? (
        <p className="page-status">불러오는 중...</p>
      ) : (
        <div className="calendar-grid">
          {WEEKDAYS.map((weekday) => (
            <div key={weekday} className="calendar-weekday">
              {weekday}
            </div>
          ))}
          {cells.map((day, i) => {
            if (day === null) {
              return <div key={`empty-${i}`} className="calendar-day empty" />;
            }
            const key = dateKey(year, month, day);
            const count = counts[key] ?? 0;
            const classes = ["calendar-day"];
            if (key === selectedDate) classes.push("selected");
            if (key === todayKey) classes.push("today");
            return (
              <button
                key={key}
                type="button"
                className={classes.join(" ")}
                onClick={() => handleSelectDay(key)}
              >
                <span>{day}</span>
                {count > 0 && <span className="calendar-day-dot" title={`독후감 ${count}건`} />}
              </button>
            );
          })}
        </div>
      )}

      {selectedDate && (
        <div className="calendar-day-panel">
          <p className="index-card-meta" style={{ margin: "0 0 8px" }}>
            {selectedDate} 작성한 독후감
          </p>
          {isDayLoading && <p className="page-status">불러오는 중...</p>}
          {!isDayLoading && dayReviews.length === 0 && (
            <p className="page-status">이 날 작성한 독후감이 없습니다.</p>
          )}
          {!isDayLoading &&
            dayReviews.map((review) => (
              <div key={review.id} className="card" style={{ marginTop: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                  <Link to={`/books/${review.book.id}`}>
                    <strong>{review.book.title}</strong>
                  </Link>
                  <span style={{ color: "var(--brass-strong)" }}>
                    {"★".repeat(review.rating)}
                    {"☆".repeat(5 - review.rating)}
                  </span>
                </div>
                <p style={{ margin: "8px 0 0" }}>{review.summary_preview}</p>
              </div>
            ))}
        </div>
      )}
    </section>
  );
}
