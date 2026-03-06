import { ApiError } from "@/api/core/ApiError";

export function getErrorMessage(error: unknown, fallback = "Something went wrong.") {
  if (error instanceof ApiError) {
    if (
      error.body &&
      typeof error.body === "object" &&
      "detail" in error.body &&
      typeof error.body.detail === "string"
    ) {
      return error.body.detail;
    }

    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}
