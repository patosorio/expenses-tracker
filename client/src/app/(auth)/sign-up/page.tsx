'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createUserWithEmailAndPassword, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { auth } from '@/lib/firebase/config';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { FloatingInput } from '@/components/layout/floating-input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { checkPasswordStrength } from '@/lib/utils/password';
import { createUser } from '@/api/users';
import { verifyToken } from '@/api/auth';

export default function SignUp() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isCompany, setIsCompany] = useState(false);
  const [companyName, setCompanyName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({ score: 0, feedback: 'Too weak' });

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    setPasswordStrength(checkPasswordStrength(value));
  };

  const getStrengthColor = (score: number) => {
    switch (score) {
      case 0: return 'bg-destructive/50';
      case 1: return 'bg-destructive';
      case 2: return 'bg-yellow-500';
      case 3: return 'bg-yellow-600';
      case 4: return 'bg-green-500';
      default: return 'bg-muted';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (passwordStrength.score < 2) {
      setError('Please choose a stronger password');
      setLoading(false);
      return;
    }

    try {
      // Create Firebase user
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      
      try {
        // Create user in backend
        await createUser({
          firebase_uid: user.uid,
          email: user.email!,
          full_name: name,
          company: isCompany ? companyName : undefined,
          user_type: isCompany ? 'business' : 'personal',
        });

        // Get token and verify it works
        const token = await user.getIdToken();
        await verifyToken(token);

        setSuccess('Account created successfully!');
        router.push('/dashboard');
      } catch (error: any) {
        console.error('Backend error:', error);
        setError('Failed to create account in our system. Please try signing in.');
        router.push('/sign-in');
      }
    } catch (error: any) {
      console.error('Firebase error:', error);
      setError(
        error.code === 'auth/email-already-in-use'
          ? 'Email already in use'
          : 'Failed to create account. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      const user = result.user;

      try {
        // Create user in backend
        await createUser({
          firebase_uid: user.uid,
          email: user.email!,
          full_name: user.displayName || undefined,
          company: isCompany ? companyName : undefined,
          user_type: isCompany ? 'business' : 'personal',
        });

        // Get token and verify it works
        const token = await user.getIdToken();
        await verifyToken(token);

        router.push('/dashboard');
      } catch (error: any) {
        console.error('Backend error:', error);
        setError('Failed to create account in our system. Please try signing in.');
        router.push('/sign-in');
      }
    } catch (error: any) {
      console.error('Firebase error:', error);
      setError('Failed to sign up with Google. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-light">Create account</CardTitle>
          <CardDescription className="text-sm">Start tracking your household expenses</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <FloatingInput
              label="Full name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <FloatingInput
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <div className="space-y-2">
              <FloatingInput
                label="Password"
                type="password"
                value={password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                required
                minLength={8}
              />
              {password && (
                <div className="space-y-1">
                  <div className="flex gap-1 h-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={`flex-1 rounded-full ${
                          i < passwordStrength.score
                            ? getStrengthColor(passwordStrength.score)
                            : 'bg-muted'
                        }`}
                      />
                    ))}
                  </div>
                  <p className={`text-xs ${
                    getStrengthColor(passwordStrength.score).replace('bg-', 'text-')
                  }`}>
                    Password strength: {passwordStrength.feedback}
                  </p>
                </div>
              )}
            </div>
            <FloatingInput
              label="Confirm password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
            />

            <div className="flex items-center space-x-2">
              <Switch
                id="company-mode"
                checked={isCompany}
                onCheckedChange={setIsCompany}
              />
              <Label htmlFor="company-mode">I'm registering as a company</Label>
            </div>

            {isCompany && (
              <FloatingInput
                label="Company name"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required={isCompany}
              />
            )}

            {error && (
              <div className="p-3 text-sm rounded-md bg-destructive/10 text-destructive">
                {error}
              </div>
            )}
            {success && (
              <div className="p-3 text-sm rounded-md bg-green-500/10 text-green-500">
                {success}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Creating account..." : "Create account"}
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Or continue with
                </span>
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleGoogleSignUp}
              disabled={loading}
            >
              <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Continue with Google
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/sign-in" className="text-foreground hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
