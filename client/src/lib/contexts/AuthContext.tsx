'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut, User, onAuthStateChanged } from 'firebase/auth';
import { auth } from '@/lib/firebase/config';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import { UserProfile } from '@/lib/types/user';

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
  isTokenVerified: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  token: null,
  login: async () => {},
  signup: async () => {},
  logout: async () => {},
  isLoading: true,
  isTokenVerified: false,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTokenVerified, setIsTokenVerified] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setUser(user);
      setProfile(null); // Reset profile when auth state changes
      setIsTokenVerified(false);
      
      if (user) {
        try {
          const token = await user.getIdToken();
          setToken(token);
          localStorage.setItem('auth_token', token);
          
          // Try to verify token with backend, but don't fail completely if it doesn't work
          try {
            const response = await authApi.verifyToken(token);
            setProfile(response.user);
            setIsTokenVerified(true);
          } catch (verifyError) {
            console.warn('Token verification failed, but user is still authenticated:', verifyError);
            // Don't sign out the user, just mark token as not verified
            // The user can still use the app, but some features might be limited
            setIsTokenVerified(false);
          }
        } catch (error) {
          console.error('Error getting token:', error);
          // Only sign out if we can't get the token at all
          await signOut(auth);
          setUser(null);
          setToken(null);
          localStorage.removeItem('auth_token');
        }
      } else {
        setToken(null);
        localStorage.removeItem('auth_token');
        setIsTokenVerified(false);
      }
      
      setIsLoading(false);
    });

    // Periodic token refresh every 45 minutes (Firebase tokens expire in 1 hour)
    const refreshInterval = setInterval(async () => {
      const currentUser = auth.currentUser;
      if (currentUser) {
        try {
          const newToken = await currentUser.getIdToken(true); // Force refresh
          setToken(newToken);
          localStorage.setItem('auth_token', newToken);
          
          // Try to verify the new token
          try {
            const response = await authApi.verifyToken(newToken);
            setProfile(response.user);
            setIsTokenVerified(true);
          } catch (verifyError) {
            console.warn('Token verification failed during refresh:', verifyError);
            setIsTokenVerified(false);
          }
        } catch (error) {
          console.error('Token refresh failed:', error);
          await signOut(auth);
          setUser(null);
          setToken(null);
          setProfile(null);
          localStorage.removeItem('auth_token');
          setIsTokenVerified(false);
        }
      }
    }, 45 * 60 * 1000); // 45 minutes instead of 50

    return () => {
      unsubscribe();
      clearInterval(refreshInterval);
    };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      await signInWithEmailAndPassword(auth, email, password);
      // Token will be set by onAuthStateChanged
      router.push('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const signup = async (email: string, password: string) => {
    try {
      await createUserWithEmailAndPassword(auth, email, password);
      // Token will be set by onAuthStateChanged
      router.push('/dashboard');
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
      setUser(null);
      setToken(null);
      setProfile(null);
      localStorage.removeItem('auth_token');
      setIsTokenVerified(false);
      router.push('/sign-in');
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, profile, token, login, signup, logout, isLoading, isTokenVerified }}>
      {children}
    </AuthContext.Provider>
  );
};