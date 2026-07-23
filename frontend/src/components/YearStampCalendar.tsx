import { useEffect, useState } from "react";
import { getCalendarDay, getCalendarYear } from "../api/stats";
import { extractErrorMessage } from "../api/errors";
import { dateKey } from "../utils/date";
import type { CalendarCounts, CalendarDayReview } from "../types/stats";

const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1);

/** stable "hand-stamped" tilt per date, not a fresh random angle on every render */
function stampRotation(key: string): number {
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    hash = (hash * 31 + key.charCodeAt(i)) % 1000;
  }
  return (hash % 17) - 8;
}

function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

export function YearStampCalendar() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [counts, setCounts] = useState<CalendarCounts>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [hoveredDate, setHoveredDate] = useState<string | null>(null);
  const [dayDetails, setDayDetails] = useState<Record<string, CalendarDayReview[]>>({});

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setHoveredDate(null);
    getCalendarYear(year)
      .then((data) => {
        if (cancelled) return;
        setCounts(data);
        setError(null);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "독서 기록을 불러오지 못했습니다."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [year]);

  function handleHover(key: string) {
    setHoveredDate(key);
    if (!(key in dayDetails)) {
      getCalendarDay(key)
        .then((data) => setDayDetails((prev) => ({ ...prev, [key]: data })))
        .catch(() => setDayDetails((prev) => ({ ...prev, [key]: [] })));
    }
  }

  function handleUnhover() {
    setHoveredDate(null);
  }

  return (
    <section className="card">
      <div className="calendar-header">
        <button className="btn" onClick={() => setYear((y) => y - 1)} aria-label="이전 연도">
          ◀
        </button>
        <h3 style={{ margin: 0 }}>{year}년의 독서 기록</h3>
        <button className="btn" onClick={() => setYear((y) => y + 1)} aria-label="다음 연도">
          ▶
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}
      {isLoading ? (
        <p className="page-status">불러오는 중...</p>
      ) : (
        <div className="stamp-cards">
          {MONTHS.map((month) => (
            <div key={month} className="stamp-card">
              <p className="stamp-card-header">
                {year}년 {month}월
              </p>
              <div className="stamp-card-days">
                {Array.from({ length: daysInMonth(year, month) }, (_, i) => i + 1).map((day) => {
                  const key = dateKey(year, month, day);
                  const count = counts[key] ?? 0;
                  const registered = count > 0;
                  const details = dayDetails[key];

                  return (
                    <div
                      key={key}
                      className={`stamp-day ${registered ? "stamp-day-registered" : "stamp-day-blank"}`}
                      tabIndex={registered ? 0 : undefined}
                      onMouseEnter={registered ? () => handleHover(key) : undefined}
                      onMouseLeave={registered ? handleUnhover : undefined}
                      onFocus={registered ? () => handleHover(key) : undefined}
                      onBlur={registered ? handleUnhover : undefined}
                    >
                      {registered ? (
                        <span
                          className={`stamp-ink${count > 1 ? " stamp-ink-multi" : ""}`}
                          style={{ transform: `rotate(${stampRotation(key)}deg)` }}
                        >
                          {day}
                        </span>
                      ) : (
                        <span>{day}</span>
                      )}

                      {registered && hoveredDate === key && (
                        <div className="stamp-tooltip">
                          <p className="stamp-tooltip-date">{key}</p>
                          {details === undefined && "불러오는 중..."}
                          {details && details.length === 0 && "등록한 독후감이 없습니다."}
                          {details && details.length > 0 && (
                            <ul>
                              {details.map((review) => (
                                <li key={review.id}>{review.book.title}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
