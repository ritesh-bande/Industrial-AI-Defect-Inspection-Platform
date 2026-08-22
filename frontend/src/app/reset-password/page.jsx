"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { resetPassword } from "../../services/authApi";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!token) {
      setError("This password reset link is invalid or has expired.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, password);
      setSuccess(true);
    } catch (err) {
      setError(err.message || "This password reset link is invalid or has expired.");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div style={{ textAlign: "center", padding: "1rem 0" }}>
        <div style={{ marginBottom: "1rem", color: "#4ade80", fontSize: "1.2rem", fontWeight: 600 }}>
          ✓ Your password has been reset successfully.
        </div>
        <p className="cyber-subtitle" style={{ marginBottom: "1.5rem" }}>
          You can now sign in to your account with your new password.
        </p>
        <Link href="/login" className="cyber-primary-btn" style={{ textDecoration: "none", display: "inline-block" }}>
          Back to Sign In
        </Link>
      </div>
    );
  }

  return (
    <form className="cyber-form" onSubmit={handleSubmit}>
      {!token ? (
        <p className="cyber-error" style={{ marginBottom: "1rem" }}>
          This password reset link is invalid or missing a security token.
        </p>
      ) : null}

      <div className="cyber-field">
        <label className="cyber-label">New Password</label>
        <div className="password-input-wrap">
          <input
            type={showPassword ? "text" : "password"}
            className="cyber-input"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
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

      <div className="cyber-field">
        <label className="cyber-label">Confirm Password</label>
        <input
          type={showPassword ? "text" : "password"}
          className="cyber-input"
          placeholder="••••••••"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
      </div>

      {error ? <p className="cyber-error">{error}</p> : null}

      <button type="submit" className="cyber-primary-btn" disabled={loading || !token}>
        {loading ? "Updating Password..." : "Reset Password"}
      </button>

      <div style={{ marginTop: "1rem", textAlign: "center" }}>
        <Link href="/login" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.9rem", fontWeight: 500 }}>
          ← Back to Sign In
        </Link>
      </div>
    </form>
  );
}

export default function ResetPasswordPage() {
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
            <span className="cyber-brand-text">VisionInspect AI</span>
          </div>

          <h1 className="cyber-title">Reset Password</h1>
          <p className="cyber-subtitle">
            Enter a new password for your VisionInspect AI account.
          </p>

          <Suspense fallback={<p style={{ color: "#94a3b8" }}>Loading security parameters...</p>}>
            <ResetPasswordForm />
          </Suspense>
        </section>

        {/* Right Graphic Section */}
        <section className="cyber-graphic-section">
          <div className="cyber-shield-glow" />
          <div className="cyber-graphic-content">
            <svg width="180" height="180" viewBox="0 0 24 24" fill="none" stroke="#0284c7" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <h2 className="cyber-graphic-title">CREDENTIAL RECOVERY</h2>
            <p className="cyber-graphic-desc">Bcrypt hash updates with immediate session invalidation.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
