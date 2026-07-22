import { isAxiosError } from "axios";
import type { ApiErrorBody } from "../types/common";

export function extractErrorMessage(error: unknown, fallback = "요청 중 오류가 발생했습니다."): string {
  if (isAxiosError(error)) {
    const body = error.response?.data as ApiErrorBody | undefined;
    const detail = body?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((item) => item.msg).join(", ");
    }
  }
  return fallback;
}
