import { request } from "@/api/core/request";
import type { GoLiveRequest } from "@/api/models/GoLiveRequest";
import type { GoOfflineRequest } from "@/api/models/GoOfflineRequest";
import type { LiveStreamerResponse } from "@/api/models/LiveStreamerResponse";
import type { LiveStreamersResponse } from "@/api/models/LiveStreamersResponse";
import type { SuccessResponse } from "@/api/models/SuccessResponse";

export class StreamsService {
  static getLive(params?: { exclude_channel_login?: string; limit?: number }) {
    return request<LiveStreamersResponse>({
      method: "GET",
      path: "/api/streams/live",
      query: params,
    });
  }

  static goLive(body: GoLiveRequest) {
    return request<LiveStreamerResponse>({
      method: "POST",
      path: "/api/streams/go-live",
      body,
    });
  }

  static goOffline(body: GoOfflineRequest) {
    return request<SuccessResponse>({
      method: "POST",
      path: "/api/streams/go-offline",
      body,
    });
  }
}
