'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { updateUserProfile, getCurrentUserProfile } from '@/api/users';
import { UserProfile as UserProfileType } from '@/types/user';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function UserProfile() {
  const { user, token } = useAuth();
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (token) {
      fetchProfile();
    }
  }, [token]);

  const fetchProfile = async () => {
    if (!token) return;
    try {
      const response = await getCurrentUserProfile(token);
      setProfile(response);
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (formData: Partial<UserProfileType>) => {
    if (!token) return;
    setSaving(true);
    try {
      const response = await updateUserProfile(token, formData);
      setProfile(response);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">User Profile</h1>
          <Button
            onClick={() => setIsEditing(!isEditing)}
            variant={isEditing ? 'secondary' : 'default'}
          >
            {isEditing ? 'Cancel' : 'Edit Profile'}
          </Button>
        </div>

        {isEditing ? (
          <EditProfileForm 
            profile={profile} 
            onSave={handleSave} 
            saving={saving} 
          />
        ) : (
          <ProfileView profile={profile} />
        )}
      </div>
    </div>
  );
}

function ProfileView({ profile }: { profile: UserProfileType | null }) {
  if (!profile) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <p className="mt-1 text-sm text-gray-900">{profile.email}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Full Name</label>
          <p className="mt-1 text-sm text-gray-900">{profile.full_name || 'Not set'}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Company</label>
          <p className="mt-1 text-sm text-gray-900">{profile.company || 'Not set'}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Role</label>
          <p className="mt-1 text-sm text-gray-900">{profile.role}</p>
        </div>
      </div>
    </div>
  );
}

function EditProfileForm({ 
  profile, 
  onSave, 
  saving 
}: { 
  profile: UserProfileType | null; 
  onSave: (data: Partial<UserProfileType>) => void;
  saving: boolean;
}) {
  const [formData, setFormData] = useState({
    full_name: profile?.full_name || '',
    company: profile?.company || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex flex-col gap-2">
          <label htmlFor="full_name" className="text-sm font-medium">Full Name</label>
          <Input
            id="full_name"
            value={formData.full_name}
            onChange={(e) => setFormData({...formData, full_name: e.target.value})}
          />
        </div>
        <div className="flex flex-col gap-2">
          <label htmlFor="company" className="text-sm font-medium">Company</label>
          <Input
            id="company"
            value={formData.company}
            onChange={(e) => setFormData({...formData, company: e.target.value})}
          />
        </div>
      </div>
      
      <div className="flex justify-end space-x-2">
        <Button
          type="submit"
          disabled={saving}
          variant="default"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </form>
  );
}