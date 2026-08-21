"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getAuthToken } from "../services/api";
import { getCurrentUser } from "../services/authApi";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function AppShell({ title, subtitle, children, variant = "" }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    getCurrentUser()
      .then((u) => {
        setUser(u);
        setReady(true);
      })
      .catch((err) => {
        if (err?.status === 401 || err?.status === 403 || err?.code === "UNAUTHORIZED") {
          setAuthToken(null);
          router.replace("/login");
        } else {
          // Network connection error fallback for offline UI development
          setUser({
            id: 1,
            username: "Quality Engineer",
            email: "admin@visioninspect.ai",
            role: "quality_engineer",
            is_active: true,
          });
          setReady(true);
        }
      });
  }, [router]);

  function handleSidebarToggle() {
    setSidebarCollapsed((current) => !current);
  }

  if (!ready) {
    return (
      <main className="loading-screen">
        <div className="loader" />
      </main>
    );
  }

  return (
    <div
      className={`app-layout${sidebarCollapsed ? " sidebar-collapsed" : ""}${variant ? ` ${variant}` : ""}`}
    >
      <Sidebar user={user} collapsed={sidebarCollapsed} onToggleCollapse={handleSidebarToggle} />
      <div className="app-main">
        <Navbar title={title} subtitle={subtitle} user={user} />
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}
