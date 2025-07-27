import { TokenResponse } from '@/lib/types/user';
import { apiClient } from './client';

export class AuthApi {
  /**
   * Verify a token with the backend
   */
  async verifyToken(token: string): Promise<TokenResponse> {
    // Token is passed as argument, so just ensure it's the JWT from localStorage 'auth_token'
    const response = await apiClient.post<TokenResponse>('/auth/verify', undefined, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.data;
  }

  /**
   * Logout the current user
   */
  async logout(): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/auth/logout');
    return response.data;
  }

  /**
   * Reset password for a user
   */
  async resetPassword(email: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/auth/reset-password', { email });
    return response.data;
  }
}

// Export a singleton instance
export const authApi = new AuthApi(); 