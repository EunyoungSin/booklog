import { useEffect, useState } from "react";
import { getMonthlyStats } from "../api/stats";
import { extractErrorMessage } from "../api/errors";
import { MonthlyCalendar } from "../components/MonthlyCalendar";
import { YearStampCalendar } from "../components/YearStampCalendar";
import type { MonthlyStats } from "../types/stats";

function currentYearMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

type StatsTab = "monthly" | "yearly";

export function StatsPage() {
  const [tab, setTab] = useState<StatsTab>("monthly");
  const [yearMonth, setYearMonth] = useState(currentYearMonth());
  const [stats, setStats] = useState<MonthlyStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const [year, month] = yearMonth.split("-").map(Number);
    if (!year || !month) return;

    let cancelled = false;
    setIsLoading(true);
    getMonthlyStats(year, month)
      .then((data) => {
        if (cancelled) return;
        setStats(data);
        setError(null);
      })
      .catch((err) => {
        if (!cancelled) setError(extractErrorMessage(err, "통계를 불러오지 못했습니다."));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [yearMonth]);

  return (
    <div>
      <h1>독서 통계</h1>

      <div className="stats-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "monthly"}
          className={`stats-tab${tab === "monthly" ? " active" : ""}`}
          onClick={() => setTab("monthly")}
        >
          월별
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "yearly"}
          className={`stats-tab${tab === "yearly" ? " active" : ""}`}
          onClick={() => setTab("yearly")}
        >
          연도별
        </button>
      </div>

      {tab === "monthly" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
          <div>
            <h2 style={{ marginTop: 0 }}>월별 통계</h2>

            <label className="form" style={{ maxWidth: 200 }}>
              조회할 월
              <input type="month" value={yearMonth} onChange={(e) => setYearMonth(e.target.value)} />
            </label>

            {isLoading && <p className="page-status">불러오는 중...</p>}
            {error && <p className="error-text">{error}</p>}

            {stats && !isLoading && (
              <div
                style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginTop: 24 }}
              >
                <div className="card" style={{ textAlign: "center" }}>
                  <p className="muted" style={{ margin: 0 }}>
                    등록한 책
                  </p>
                  <p style={{ fontSize: 32, fontWeight: 700, margin: "8px 0 0" }}>
                    {stats.books_added_count}
                  </p>
                </div>
                <div className="card" style={{ textAlign: "center" }}>
                  <p className="muted" style={{ margin: 0 }}>
                    작성한 독후감
                  </p>
                  <p style={{ fontSize: 32, fontWeight: 700, margin: "8px 0 0" }}>
                    {stats.reviews_written_count}
                  </p>
                </div>
                <div className="card" style={{ textAlign: "center" }}>
                  <p className="muted" style={{ margin: 0 }}>
                    평균 별점
                  </p>
                  <p style={{ fontSize: 32, fontWeight: 700, margin: "8px 0 0" }}>
                    {stats.average_rating !== null ? stats.average_rating.toFixed(1) : "-"}
                  </p>
                </div>
              </div>
            )}
          </div>

          <div>
            <h2 style={{ marginTop: 0 }}>월간 캘린더</h2>
            <MonthlyCalendar />
          </div>
        </div>
      )}

      {tab === "yearly" && <YearStampCalendar />}
    </div>
  );
}
