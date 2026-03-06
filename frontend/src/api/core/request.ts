import { ApiError } from "@/api/core/ApiError";
import { OpenAPI } from "@/api/core/OpenAPI";

type QueryValue = string | number | boolean | null | undefined;

interface RequestOptions {
  method: "GET" | "POST";
  path: string;
  body?: unknown;
  query?: Record<string, QueryValue>;
}

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const url = new URL(`${OpenAPI.BASE}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === null || value === undefined || value === "") {
        continue;
      }
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export async function request<T>({ method, path, body, query }: RequestOptions): Promise<T> {
  const response = await fetch(buildUrl(path, query), {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
    cache: "no-store",
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = (await response.json()) as unknown;
  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`;
    throw new ApiError(
      response.status,
      payload,
      typeof payload === "object" && payload && "detail" in payload && typeof payload.detail === "string"
        ? payload.detail
        : fallback,
    );
  }

  return payload as T;
}
