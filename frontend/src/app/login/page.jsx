"use client";

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

import { login, registerUser } from "../../services/authApi";
import { setAuthToken } from "../../services/api";

export default function LoginPage() {
  const [mode, setMode] = useState("login");
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "quality_engineer",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    // --- Client-side format validation ---
    if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setError("Please enter a valid email address.");
      return;
    }
    if (!form.password || form.password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);

    try {
      if (mode === "login") {
        const authData = await login({ email: form.email, password: form.password });
        if (authData && authData.access_token) {
          window.location.href = "/dashboard";
        } else {
          setAuthToken(null);
          setError("Invalid email or password.");
        }
      } else {
        const result = await registerUser(form);
        if (result && result.access_token) {
          window.location.href = "/dashboard";
        } else {
          setSuccess("Account registered successfully. Please sign in.");
          setMode("login");
        }
      }
    } catch (err) {
      setAuthToken(null); // Clear any stored token on failed login
      const status = err.status;
      if (status === 403) {
        setError(err.message || "User account is disabled.");
      } else if (status === 401) {
        setError("Invalid email or password.");
      } else if (status === 400 || status === 422) {
        setError(err.message || "Invalid credentials format.");
      } else {
        setError(err.message || "Invalid email or password.");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSocialLogin(provider) {
    setError(`Social SSO with ${provider} is not enabled. Please sign in with your email and password.`);
  }

  return (
    <main className="cyber-page-wrapper">
      <div className="cyber-login-card">
        {/* Left Form Section */}
        <section className="cyber-form-section">
          <div className="cyber-brand-header">
            <span className="cyber-brand-mark">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </span>
            <span className="cyber-brand-name">VisionInspect AI</span>
          </div>

          <h1 className="cyber-title">
            {mode === "login" ? "Sign in" : "Sign up"}
          </h1>

          <p className="cyber-subtitle">
            {mode === "login" ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              className="cyber-link-btn"
              onClick={() => {
                setError("");
                setSuccess("");
                setMode(mode === "login" ? "register" : "login");
              }}
            >
              {mode === "login" ? "Create now" : "Sign in here"}
            </button>
          </p>

          <form onSubmit={handleSubmit} className="cyber-form">
            {mode === "register" ? (
              <>
                <div className="cyber-field">
                  <label className="cyber-label">Full Name</label>
                  <input
                    type="text"
                    className="cyber-input"
                    placeholder="Enter your name"
                    value={form.name}
                    onChange={(e) => updateField("name", e.target.value)}
                    required
                  />
                </div>
                <div className="cyber-field">
                  <label className="cyber-label">Role</label>
                  <select
                    className="cyber-input cyber-select"
                    value={form.role}
                    onChange={(e) => updateField("role", e.target.value)}
                  >
                    <option value="quality_engineer">Quality Engineer</option>
                    <option value="factory_supervisor">Factory Supervisor</option>
                    <option value="quality_manager">Quality Manager</option>
                  </select>
                </div>
              </>
            ) : null}

            <div className="cyber-field">
              <label className="cyber-label">Email</label>
              <input
                type="email"
                className="cyber-input"
                placeholder="example@gmail.com"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                required
              />
            </div>

            <div className="cyber-field">
              <label className="cyber-label">Password</label>
              <div className="password-input-wrap">
                <input
                  type={showPassword ? "text" : "password"}
                  className="cyber-input"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => updateField("password", e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error ? <p className="cyber-error">{error}</p> : null}
            {success ? <p className="cyber-success">{success}</p> : null}

            <button type="submit" className="cyber-primary-btn" disabled={loading}>
              {loading ? "Processing..." : mode === "login" ? "Sign in" : "Create Account"}
            </button>
          </form>

          {/* OR Divider */}
          <div className="cyber-divider">
            <span>OR</span>
          </div>

          {/* Social SSO Buttons */}
          <div className="social-sso-group">
            <button
              type="button"
              className="sso-btn"
              onClick={() => handleSocialLogin("Google")}
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Continue with Google</span>
            </button>

            <button
              type="button"
              className="sso-btn"
              onClick={() => handleSocialLogin("Facebook")}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="#1877F2">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
              </svg>
              <span>Continue with Facebook</span>
            </button>
          </div>
        </section>

        {/* Right Graphic Section */}
        <section className="cyber-graphic-section">
          <div className="cyber-graphic-bg" />
        </section>
      </div>
    </main>
  );
}
