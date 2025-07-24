import { UserProfile } from '@/lib/types/user';
import { apiClient } from './client';

export class UsersApi {
  /**
   * Create a new user
   */
  async createUser(data: {
    firebase_uid: string;
    email: string;
    full_name?: string;
    company?: string;
    user_type: 'personal' | 'business';
  }): Promise<UserProfile> {
    const response = await apiClient.post<UserProfile>('/users', data);
    return response.data;
  }

  /**
   * Get current user profile
   */
  async getCurrentUserProfile(token: string): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>('/users/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  /**
   * Update current user profile
   */
  async updateUserProfile(token: string, data: {
    full_name?: string;
    company?: string;
    avatar_url?: string;
  }): Promise<UserProfile> {
    const response = await apiClient.put<UserProfile>('/users/me', data, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  /**
   * Get all users (Admin/Manager only)
   */
  async getUsers(
    token: string,
    params: {
      skip?: number;
      limit?: number;
      role?: string;
      status?: string;
      search?: string;
    } = {}
  ): Promise<{ users: UserProfile[]; total: number; page: number; per_page: number; pages: number }> {
    const queryParams = new URLSearchParams();
    if (params.skip) queryParams.append('skip', params.skip.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.role) queryParams.append('role', params.role);
    if (params.status) queryParams.append('status', params.status);
    if (params.search) queryParams.append('search', params.search);

    const response = await apiClient.get<{ users: UserProfile[]; total: number; page: number; per_page: number; pages: number }>(`/users?${queryParams}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  /**
   * Get user by ID (Admin/Manager only)
   */
  async getUserById(token: string, userId: string): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>(`/users/${userId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  /**
   * Update user by ID (Admin/Manager only)
   */
  async updateUser(
    token: string,
    userId: string,
    data: {
      full_name?: string;
      company?: string;
    }
  ): Promise<UserProfile> {
    const response = await apiClient.put<UserProfile>(`/users/${userId}`, data, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  /**
   * Deactivate user by ID (Admin/Manager only)
   */
  async deactivateUser(token: string, userId: string): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`/users/${userId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }
}

// Export a singleton instance
export const usersApi = new UsersApi(); 