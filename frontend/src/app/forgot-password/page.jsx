"use client";

import { useState } from "react";
import Link from "next/link";
import { requestPasswordReset } from "../../services/authApi";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    if (!email.trim()) {
      setError("Please enter a valid email address.");
      return;
    }

    setLoading(true);
    try {
      const res = await requestPasswordReset(email.trim());
      setMessage(res?.message || "If an account exists for this email, a password reset link has been sent.");
    } catch (err) {
      // Always show generic message to prevent email enumeration
      setMessage("If an account exists for this email, a password reset link has been sent.");
    } finally {
      setLoading(false);
    }
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
            <span className="cyber-brand-text">VisionInspect AI</span>
          </div>

          <h1 className="cyber-title">Forgot your password?</h1>
          <p className="cyber-subtitle">
            Enter the email address associated with your VisionInspect AI account.
          </p>

          <form className="cyber-form" onSubmit={handleSubmit}>
            <div className="cyber-field">
              <label className="cyber-label">Email Address</label>
              <input
                type="email"
                className="cyber-input"
                placeholder="example@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {error ? <p className="cyber-error">{error}</p> : null}
            {message ? <p className="cyber-success">{message}</p> : null}

            <button type="submit" className="cyber-primary-btn" disabled={loading}>
              {loading ? "Sending Request..." : "Send Reset Link"}
            </button>

            <div style={{ marginTop: "1rem", textAlign: "center" }}>
              <Link href="/login" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.9rem", fontWeight: 500 }}>
                ← Back to Sign In
              </Link>
            </div>
          </form>
        </section>

        {/* Right Graphic Section */}
        <section className="cyber-graphic-section">
          <div className="cyber-shield-glow" />
          <div className="cyber-graphic-content">
            <svg width="180" height="180" viewBox="0 0 24 24" fill="none" stroke="#0284c7" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <rect x="9" y="11" width="6" height="5" rx="1" stroke="#38bdf8" strokeWidth="1.5"/>
              <path d="M10 11V9a2 2 0 1 1 4 0v2" stroke="#38bdf8" strokeWidth="1.5"/>
            </svg>
            <h2 className="cyber-graphic-title">SECURE ACCOUNT RECOVERY</h2>
            <p className="cyber-graphic-desc">Cryptographically signed single-use authentication tokens.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
