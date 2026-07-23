import { apiClient } from "./client";
import type { CalendarCounts, CalendarDayReview, MonthlyStats } from "../types/stats";

export async function getMonthlyStats(year: number, month: number): Promise<MonthlyStats> {
  const res = await apiClient.get<MonthlyStats>("/api/stats/monthly", {
    params: { year, month },
  });
  return res.data;
}

export async function getCalendarMonth(year: number, month: number): Promise<CalendarCounts> {
  const res = await apiClient.get<CalendarCounts>("/api/stats/calendar", {
    params: { year, month },
  });
  return res.data;
}

export async function getCalendarYear(year: number): Promise<CalendarCounts> {
  const res = await apiClient.get<CalendarCounts>("/api/stats/calendar/year", {
    params: { year },
  });
  return res.data;
}

export async function getCalendarDay(date: string): Promise<CalendarDayReview[]> {
  const res = await apiClient.get<CalendarDayReview[]>("/api/stats/calendar/day", {
    params: { date },
  });
  return res.data;
}
