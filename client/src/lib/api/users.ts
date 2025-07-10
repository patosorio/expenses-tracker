import { UserProfile } from '@/lib/types/user';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function createUser(data: {
  firebase_uid: string;
  email: string;
  full_name?: string;
  company?: string;
  user_type: 'personal' | 'business';
}): Promise<UserProfile> {
  const response = await fetch(`${API_URL}/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to create user');
  }

  return response.json();
}

export async function getCurrentUserProfile(token: string): Promise<UserProfile> {
  const response = await fetch(`${API_URL}/users/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get current user profile');
  }

  return response.json();
}

export async function updateUserProfile(token: string, data: {
  full_name?: string;
  company?: string;
  avatar_url?: string;
}): Promise<UserProfile> {
  const response = await fetch(`${API_URL}/users/me`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update user profile');
  }

  return response.json();
}

// Admin/Manager only endpoints
export async function getUsers(
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

  const response = await fetch(`${API_URL}/users?${queryParams}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get users');
  }

  return response.json();
}

export async function getUserById(token: string, userId: string): Promise<UserProfile> {
  const response = await fetch(`${API_URL}/users/${userId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get user by ID');
  }

  return response.json();
}

export async function updateUser(
  token: string,
  userId: string,
  data: {
    full_name?: string;
    company?: string;
  }
): Promise<UserProfile> {
  const response = await fetch(`${API_URL}/users/${userId}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update user');
  }

  return response.json();
}

export async function deactivateUser(token: string, userId: string): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/users/${userId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to deactivate user');
  }

  return response.json();
} 