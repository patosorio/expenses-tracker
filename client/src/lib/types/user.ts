export interface UserProfile {
  id: string;
  email: string;
  firebase_uid: string;
  full_name?: string;
  company?: string;
  avatar_url: string;
  role: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
} 