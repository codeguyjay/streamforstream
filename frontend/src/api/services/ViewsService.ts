import { request } from "@/api/core/request";
import type { ReportViewRequest } from "@/api/models/ReportViewRequest";
import type { ReportViewResponse } from "@/api/models/ReportViewResponse";

export class ViewsService {
  static reportView(body: ReportViewRequest) {
    return request<ReportViewResponse>({
      method: "POST",
      path: "/api/views/report",
      body,
    });
  }
}
