import { request } from "@/api/core/request";
import type { ResolveChannelRequest } from "@/api/models/ResolveChannelRequest";
import type { ResolveChannelResponse } from "@/api/models/ResolveChannelResponse";

export class TwitchService {
  static resolveChannel(body: ResolveChannelRequest) {
    return request<ResolveChannelResponse>({
      method: "POST",
      path: "/api/twitch/resolve-channel",
      body,
    });
  }
}
