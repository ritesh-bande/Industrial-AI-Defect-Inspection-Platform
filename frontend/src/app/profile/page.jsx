"use client";

import { useEffect, useState } from "react";
import { User, Shield, KeyRound, Calendar, Mail, UserCheck } from "lucide-react";
import AppShell from "../../components/AppShell";
import { getCurrentUser } from "../../services/authApi";
import { apiPost } from "../../services/api";

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then(setProfile)
      .catch(() => {});
  }, []);

  async function handlePasswordReset(e) {
    e.preventDefault();
    setMessage("");
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setMessage("New passwords do not match.");
      return;
    }
    
    if (passwordForm.newPassword.length < 6) {
      setMessage("New password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      // Endpoint is /api/users/{user_id}/reset-password or similar. We can also call our current user reset path
      await apiPost(`/api/users/${profile.id}/reset-password`, {
        password: passwordForm.newPassword
      });
      setMessage("Password changed successfully.");
      setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    } catch (err) {
      setMessage(err.message || "Failed to reset password.");
    } finally {
      setLoading(false);
    }
  }

  function updateForm(field, val) {
    setPasswordForm(prev => ({ ...prev, [field]: val }));
  }

  return (
    <AppShell title="User Profile" subtitle="Manage your quality operator credentials and passwords.">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        
        {/* User Card */}
        <section className="tool-panel lg:col-span-1 flex flex-col items-center text-center p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mb-4">
            <User size={48} />
          </div>
          <h2 className="text-xl font-semibold text-gray-800">{profile?.username || "Quality Engineer"}</h2>
          <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full uppercase mt-2">
            {profile?.role || "Operator"}
          </span>
          
          <div className="w-full border-t border-gray-150 my-6"></div>
          
          <div className="w-full text-left space-y-4">
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <Mail size={16} className="text-gray-400" />
              <span>{profile?.email || "admin@visioninspect.ai"}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <Shield size={16} className="text-gray-400" />
              <span>Role Permissions: <b>Full Access</b></span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <Calendar size={16} className="text-gray-400" />
              <span>Joined: {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : "2026-07-22"}</span>
            </div>
          </div>
        </section>

        {/* Security / Password Reset */}
        <section className="tool-panel lg:col-span-2 bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <div className="panel-heading mb-4 flex items-center gap-3 border-b pb-4">
            <KeyRound size={22} className="text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-800">Account Security</h2>
              <p className="text-sm text-gray-500">Update your access password below.</p>
            </div>
          </div>
          
          <form onSubmit={handlePasswordReset} className="space-y-4 max-w-md">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
              <input 
                type="password" 
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={passwordForm.currentPassword}
                onChange={e => updateForm("currentPassword", e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
              <input 
                type="password" 
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={passwordForm.newPassword}
                onChange={e => updateForm("newPassword", e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
              <input 
                type="password" 
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={passwordForm.confirmPassword}
                onChange={e => updateForm("confirmPassword", e.target.value)}
                required
              />
            </div>
            
            {message && (
              <p className={`text-sm ${message.includes("successfully") ? "text-green-600" : "text-red-600"}`}>
                {message}
              </p>
            )}

            <button 
              type="submit" 
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition duration-200"
              disabled={loading}
            >
              {loading ? "Saving..." : "Change Password"}
            </button>
          </form>
        </section>

      </div>
    </AppShell>
  );
}
