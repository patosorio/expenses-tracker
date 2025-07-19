import { TokenResponse } from '@/types/user';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function verifyToken(token: string): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/verify`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to verify token' }));
    throw new Error(error.detail || 'Failed to verify token');
  }

  return response.json();
}

export async function logout(): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/auth/logout`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to logout');
  }

  return response.json();
}

export async function resetPassword(email: string): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/auth/reset-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to send reset email' }));
    throw new Error(error.detail || 'Failed to send reset email');
  }

  return response.json();
} 