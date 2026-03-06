import type { LiveStreamerResponse } from "@/api/models/LiveStreamerResponse";

export interface LiveStreamersResponse {
  items: LiveStreamerResponse[];
  checked_at: string;
  viewer_total_points: number;
  viewer_is_live: boolean;
  next_cursor?: string | null;
  has_more: boolean;
}
