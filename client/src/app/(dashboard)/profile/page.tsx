'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/contexts/AuthContext';
import { updateUserProfile, getUserProfile } from '@/lib/api/users';
import { UserProfile as UserProfileType } from '@/lib/types/user';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function UserProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await getUserProfile();
      setProfile(response.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (formData: Partial<UserProfileType>) => {
    setSaving(true);
    try {
      const response = await updateUserProfile(formData);
      setProfile(response.data);
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
            variant={isEditing ? 'secondary' : 'primary'}
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
          <label className="block text-sm font-medium text-gray-700">Display Name</label>
          <p className="mt-1 text-sm text-gray-900">{profile.display_name || 'Not set'}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">First Name</label>
          <p className="mt-1 text-sm text-gray-900">{profile.first_name || 'Not set'}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Last Name</label>
          <p className="mt-1 text-sm text-gray-900">{profile.last_name || 'Not set'}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Company</label>
          <p className="mt-1 text-sm text-gray-900">{profile.company || 'Not set'}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-bicolor-700">Role</label>
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
    display_name: profile?.display_name || '',
    first_name: profile?.first_name || '',
    last_name: profile?.last_name || '',
    company: profile?.company || '',
    department: profile?.department || '',
    job_title: profile?.job_title || '',
    phone_number: profile?.phone_number || '',
    bio: profile?.bio || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Display Name"
          value={formData.display_name}
          onChange={(e) => setFormData({...formData, display_name: e.target.value})}
        />
        <Input
          label="First Name"
          value={formData.first_name}
          onChange={(e) => setFormData({...formData, first_name: e.target.value})}
        />
        <Input
          label="Last Name"
          value={formData.last_name}
          onChange={(e) => setFormData({...formData, last_name: e.target.value})}
        />
        <Input
          label="Company"
          value={formData.company}
          onChange={(e) => setFormData({...formData, company: e.target.value})}
        />
        <Input
          label="Department"
          value={formData.department}
          onChange={(e) => setFormData({...formData, department: e.target.value})}
        />
        <Input
          label="Job Title"
          value={formData.job_title}
          onChange={(e) => setFormData({...formData, job_title: e.target.value})}
        />
      </div>
      
      <div className="flex justify-end space-x-2">
        <Button
          type="submit"
          disabled={saving}
          variant="primary"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </form>
  );
}