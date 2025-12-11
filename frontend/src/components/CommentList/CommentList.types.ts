export interface Comment {
  id: number;
  user_id?: number;
  user?: {
    username: string;
    avatar_url?: string;
  };
  user_name?: string;
  user_email?: string;
  content: string;
  created_at: string;
  likes_count?: number;
  like_count?: number;
  user_has_liked?: boolean;
  fullName?: string;
}