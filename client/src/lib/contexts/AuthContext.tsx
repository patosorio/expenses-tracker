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
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  token: null,
  login: async () => {},
  signup: async () => {},
  logout: async () => {},
  isLoading: true,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setUser(user);
      setProfile(null); // Reset profile when auth state changes
      
      if (user) {
        try {
          const token = await user.getIdToken();
          setToken(token);
          localStorage.setItem('firebase-token', token);
          
          // Verify token with backend and get user profile
          const response = await authApi.verifyToken(token);
          setProfile(response.user);
        } catch (error) {
          console.error('Error verifying token:', error);
          // If token verification fails, sign out the user
          await signOut(auth);
          setUser(null);
          setToken(null);
          localStorage.removeItem('firebase-token');
        }
      } else {
        setToken(null);
        localStorage.removeItem('firebase-token');
      }
      
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      await signInWithEmailAndPassword(auth, email, password);
      router.push('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const signup = async (email: string, password: string) => {
    try {
      await createUserWithEmailAndPassword(auth, email, password);
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
      localStorage.removeItem('firebase-token');
      router.push('/sign-in');
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, profile, token, login, signup, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};