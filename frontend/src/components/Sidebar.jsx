"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Camera,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Cpu,
  Factory,
  FileText,
  Gauge,
  ImageUp,
  LogOut,
  ScanSearch,
  ShieldCheck,
  Wrench,
  Users,
  User,
  Settings,
} from "lucide-react";

import { logout } from "../services/authApi";

const navItems = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: Gauge,
    section: "",
    roles: ["admin", "quality_manager", "factory_supervisor", "quality_engineer"],
  },
  {
    href: "/upload",
    label: "Upload",
    icon: ImageUp,
    section: "Inspection",
    roles: ["admin", "quality_manager", "factory_supervisor", "quality_engineer"],
  },
  {
    href: "/camera",
    label: "Camera",
    icon: Camera,
    section: "Inspection",
    roles: ["admin", "quality_manager", "factory_supervisor", "quality_engineer"],
  },
  {
    href: "/inspection",
    label: "Inspection History",
    icon: ClipboardList,
    section: "Inspection",
    roles: ["admin", "quality_manager", "factory_supervisor", "quality_engineer"],
  },
  {
    href: "/rework",
    label: "Rework Queue",
    icon: Wrench,
    section: "Rework",
    roles: ["admin", "quality_manager", "factory_supervisor"],
  },
  {
    href: "/analytics",
    label: "Analytics",
    icon: BarChart3,
    section: "Reports & Analytics",
    roles: ["admin", "quality_manager", "factory_supervisor"],
  },
  {
    href: "/reports",
    label: "Reports",
    icon: FileText,
    section: "Reports & Analytics",
    roles: ["admin", "quality_manager", "factory_supervisor", "quality_engineer"],
  },
  {
    href: "/model-metrics",
    label: "Model Metrics",
    icon: ScanSearch,
    section: "Models",
    roles: ["admin", "quality_manager"],
  },
  {
    href: "/finetune",
    label: "Fine-Tune Models",
    icon: Cpu,
    section: "Models",
    roles: ["admin", "quality_manager"],
  },
  { href: "/users", label: "Users", icon: Users, section: "Admin", roles: ["admin", "quality_manager"] },
  {
    href: "/profile",
    label: "My Profile",
    icon: User,
    section: "Account",
    roles: ["admin", "quality_manager", "factory_supervisor", "quality_engineer", "operator"],
  },
  {
    href: "/settings",
    label: "Settings",
    icon: Settings,
    section: "Account",
    roles: ["admin", "quality_manager", "factory_supervisor", "quality_engineer", "operator"],
  },
];

export default function Sidebar({ user, collapsed = false, onToggleCollapse }) {
  const pathname = usePathname();
  const role = user?.role || "quality_engineer";

  function handleLogout() {
    logout();
    window.location.href = "/login";
  }

  const visibleItems = navItems.filter((item) => item.roles.includes(role));
  const sections = visibleItems.reduce((groups, item) => {
    const section = item.section || "Main";
    return { ...groups, [section]: [...(groups[section] || []), item] };
  }, {});

  const ToggleIcon = collapsed ? ChevronRight : ChevronLeft;

  return (
    <aside className={collapsed ? "sidebar collapsed" : "sidebar"}>
      <Link href="/dashboard" className="brand" aria-label="VisionInspect AI dashboard" data-label="VisionInspect AI">
        <span className="brand-mark">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ display: 'block' }}>
            <path d="M6 4H20L17 9H3L6 4Z" fill="var(--neon-lime)" />
            <path d="M8 11H17L14 16H5L8 11Z" fill="var(--neon-lime)" />
            <path d="M10 18H14L11 23H7L10 18Z" fill="var(--neon-lime)" />
          </svg>
        </span>
        <span>
          <strong>VisionInspect AI</strong>
          <small>Quality inspection</small>
        </span>
      </Link>

      <nav className="side-nav" aria-label="Main navigation">
        {Object.entries(sections).map(([section, items]) => (
          <div key={section} className="nav-section">
            {section !== "Main" ? <span className="nav-section-label">{section}</span> : null}
            {items.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  className={active ? "nav-link active" : "nav-link"}
                  href={item.href}
                  data-label={item.label}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="security-chip" data-label="RBAC enabled">
          <ShieldCheck size={16} />
          <span>RBAC enabled</span>
        </div>
        <button className="ghost-button full-width" type="button" onClick={handleLogout} data-label="Logout">
          <LogOut size={16} />
          <span>Logout</span>
        </button>
        <button
          className="ghost-button full-width collapse-button"
          type="button"
          onClick={onToggleCollapse}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          data-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ToggleIcon size={16} />
          <span>{collapsed ? "Expand" : "Collapse"}</span>
        </button>
      </div>
    </aside>
  );
}
