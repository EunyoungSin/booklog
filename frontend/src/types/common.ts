export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface ApiErrorBody {
  detail: string | { msg: string; loc: (string | number)[] }[];
}
