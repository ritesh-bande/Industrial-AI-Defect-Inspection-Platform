"use client";

import { useEffect, useRef, useState } from "react";
import { Bell, ChevronDown } from "lucide-react";

import { logout } from "../services/authApi";

export default function Navbar({ title, subtitle, user }) {
  const [openMenu, setOpenMenu] = useState("");
  const topbarMenuRef = useRef(null);

  function toggleMenu(menu) {
    setOpenMenu((current) => (current === menu ? "" : menu));
  }

  function handleLogout() {
    logout();
    window.location.href = "/login";
  }

  useEffect(() => {
    function handlePointerDown(event) {
      if (!topbarMenuRef.current?.contains(event.target)) {
        setOpenMenu("");
      }
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        setOpenMenu("");
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return (
    <header className="topbar">
      <div>
        <h1>{title || "VisionInspect AI"}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      <div className="topbar-actions" ref={topbarMenuRef}>
        <button
          className="icon-link search-button"
          type="button"
          aria-label="Search"
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            display: 'grid',
            placeItems: 'center',
            color: 'var(--muted)',
            cursor: 'pointer',
            marginRight: '6px'
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </button>
        <div className="topbar-menu-wrap">
          <button
            className="icon-link notification-button"
            type="button"
            aria-label="Notifications"
            onClick={() => toggleMenu("notifications")}
          >
            <Bell size={16} />
            <span>8</span>
          </button>
          {openMenu === "notifications" ? (
            <div className="topbar-dropdown notification-dropdown">
              <strong>Notifications</strong>
              <p>8 quality events need attention.</p>
              <div className="notification-list">
                <span>
                  <b>Critical defects</b>
                  <small>24 critical inspections recorded</small>
                </span>
                <span>
                  <b>Rework queue</b>
                  <small>2 products are waiting for repair action</small>
                </span>
                <span>
                  <b>Model confidence</b>
                  <small>Average confidence is stable at 84.4%</small>
                </span>
              </div>
            </div>
          ) : null}
        </div>
        {user ? (
          <div className="topbar-menu-wrap">
            <button
              className="user-pill user-menu-button"
              type="button"
              onClick={() => toggleMenu("user")}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)', borderRadius: '24px', padding: '6px 14px' }}
            >
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(212, 255, 42, 0.1)', border: '1px solid var(--neon-lime)', display: 'grid', placeItems: 'center', overflow: 'hidden' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--neon-lime)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', lineHeight: '1.2' }}>
                <strong style={{ fontSize: '13px', fontWeight: '600', color: '#ffffff' }}>{user.name || user.username}</strong>
                <small style={{ fontSize: '10px', color: 'var(--neon-lime)', display: 'flex', alignItems: 'center', gap: '2px', fontWeight: '500' }}>
                  ★ 4.9 ({user.role})
                </small>
              </div>
              <ChevronDown size={12} style={{ opacity: 0.6, marginLeft: '2px' }} />
            </button>
            {openMenu === "user" ? (
              <div className="topbar-dropdown user-dropdown">
                <strong>{user.name}</strong>
                <small>{user.email || user.role}</small>
                <div className="dropdown-divider" />
                <a href="/profile">My Profile</a>
                <a href="/settings">System Settings</a>
                <a href="/users">User Management</a>
                <a href="/model-metrics">Model Calibration</a>
                <button type="button" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </header>
  );
}
