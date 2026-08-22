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
          if (typeof window !== "undefined") {
            window.localStorage.removeItem("visioninspect_token");
          }
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
      setAuthToken(null);
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("visioninspect_token");
      }
      const status = err.status;
      if (status === 403) {
        setError(err.message || "User account is disabled.");
      } else if (status === 401) {
        setError("Invalid email or password.");
      } else if (status === 400 || status === 422) {
        setError(err.message || "Invalid credentials format.");
      } else {
        setError(err.message || "Backend authentication service offline or unreachable.");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSocialLogin(provider) {
    setAuthToken(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("visioninspect_token");
    }
    setError(`${provider} authentication is not configured. Please sign in with your email and password.`);
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
        </section>

        {/* Right Graphic Section */}
        <section className="cyber-graphic-section">
          <div className="cyber-graphic-bg" />
        </section>
      </div>
    </main>
  );
}
