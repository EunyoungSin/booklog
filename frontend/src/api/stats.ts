import { apiClient } from "./client";
import type { MonthlyStats } from "../types/stats";

export async function getMonthlyStats(year: number, month: number): Promise<MonthlyStats> {
  const res = await apiClient.get<MonthlyStats>("/api/stats/monthly", {
    params: { year, month },
  });
  return res.data;
}
