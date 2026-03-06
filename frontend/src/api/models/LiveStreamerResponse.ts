export interface LiveStreamerResponse {
  channel_login: string;
  channel_display_name: string;
  profile_image_url: string;
  channel_url: string;
  is_live: boolean;
  stream_title: string;
  game_name: string;
  viewer_count: number;
  went_live_at: string;
  total_points: number;
}
