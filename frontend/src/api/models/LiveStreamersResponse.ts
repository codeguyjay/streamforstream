import type { LiveStreamerResponse } from "@/api/models/LiveStreamerResponse";

export interface LiveStreamersResponse {
  items: LiveStreamerResponse[];
  checked_at: string;
  viewer_points_balance: number;
  viewer_is_live: boolean;
}
