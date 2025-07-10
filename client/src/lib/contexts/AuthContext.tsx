'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { User, onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '@/lib/firebase/config';
import { verifyToken } from '@/lib/api/auth';
import { UserProfile } from '@/lib/types/user';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  loading: boolean;
  token: string | null;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  loading: true,
  token: null,
  logout: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setUser(user);
      setProfile(null); // Reset profile when auth state changes
      
      if (user) {
        try {
          const token = await user.getIdToken();
          setToken(token);
          
          // Verify token with backend and get user profile
          const response = await verifyToken(token);
          setProfile(response.user);
        } catch (error) {
          console.error('Error verifying token:', error);
          // If token verification fails, sign out the user
          await auth.signOut();
          setUser(null);
          setToken(null);
          setProfile(null);
          router.push('/sign-in');
        }
      } else {
        setToken(null);
        setProfile(null);
      }
      
      setLoading(false);
    });

    return () => unsubscribe();
  }, [router]);

  const logout = async () => {
    try {
      await signOut(auth);
      setUser(null);
      setToken(null);
      setProfile(null);
      router.push('/sign-in');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, profile, loading, token, logout }}>
      {children}
    </AuthContext.Provider>
  );
};