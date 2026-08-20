"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearCompanyToken } from "@/services/companyApi";
import "./Sidebar.css";

function Icon({ path }: { path: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={path} />
    </svg>
  );
}

const ICONS = {
  dashboard: "M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z",
  leads: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7 3a4 4 0 0 0 0-8",
  agents: "M12 2a3 3 0 0 1 3 3v1h1a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3v-7a3 3 0 0 1 3-3h1V5a3 3 0 0 1 3-3ZM9 12h.01M15 12h.01M9 16h6",
  analytics: "M4 19h16M7 19V9m5 10V5m5 14v-7",
  demos: "M4 6c0-1.1 3.58-2 8-2s8 .9 8 2-3.58 2-8 2-8-.9-8-2Zm0 0v12c0 1.1 3.58 2 8 2s8-.9 8-2V6M4 12c0 1.1 3.58 2 8 2s8-.9 8-2",
  settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.3.9a7 7 0 0 0-2-1.2L14 3h-4l-.6 2.5a7 7 0 0 0-2 1.2l-2.3-.9-2 3.4 2 1.6a7 7 0 0 0 0 2.4l-2 1.6 2 3.4 2.3-.9a7 7 0 0 0 2 1.2L10 21h4l.6-2.5a7 7 0 0 0 2-1.2l2.3.9 2-3.4-2-1.6c.07-.4.1-.8.1-1.2Z",
};

const NAV_ITEMS: { key: keyof typeof ICONS; label: string; href: string }[] = [
  { key: "dashboard", label: "Dashboard", href: "/company/dashboard" },
  { key: "leads", label: "Leads", href: "/company/leads" },
  { key: "agents", label: "Agents", href: "/company/agents" },
  { key: "analytics", label: "Analytics", href: "/company/analytics" },
  { key: "demos", label: "Demos", href: "/company/demos" },
];

export default function CompanySidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    clearCompanyToken();
    router.push("/company/login");
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <Link href="/company/dashboard" className="sidebar-logo">
          <span className="sidebar-logo-mark">◈</span>
          <span className="sidebar-logo-text">
            WINFOMI
            <br />
            Instant AI
          </span>
        </Link>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.key}
              href={item.href}
              className={`sidebar-nav-item ${pathname?.startsWith(item.href) ? "is-active" : ""}`}
            >
              <Icon path={ICONS[item.key]} />
              {item.label}
            </Link>
          ))}
        </nav>

        <hr style={{ border: "none", borderTop: "1px solid var(--card-border)", margin: "4px 8px" }} />

        <nav className="sidebar-nav">
          <Link href="/company/settings" className={`sidebar-nav-item ${pathname?.startsWith("/company/settings") ? "is-active" : ""}`}>
            <Icon path={ICONS.settings} />
            Settings
          </Link>
        </nav>
      </div>

      <div className="sidebar-bottom">
        <button type="button" className="btn-secondary" style={{ width: "100%" }} onClick={handleLogout}>
          Log out
        </button>
      </div>
    </aside>
  );
}
