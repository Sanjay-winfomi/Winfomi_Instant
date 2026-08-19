"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import "./Sidebar.css";

function Icon({ path }: { path: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={path} />
    </svg>
  );
}

const ICONS = {
  agents: "M12 2a3 3 0 0 1 3 3v1h1a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3v-7a3 3 0 0 1 3-3h1V5a3 3 0 0 1 3-3ZM9 12h.01M15 12h.01M9 16h6",
  templates: "M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z",
  datasets: "M4 6c0-1.1 3.58-2 8-2s8 .9 8 2-3.58 2-8 2-8-.9-8-2Zm0 0v12c0 1.1 3.58 2 8 2s8-.9 8-2V6M4 12c0 1.1 3.58 2 8 2s8-.9 8-2",
  integrations: "M9 3v4M15 3v4M6 10h12l-1 9a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2l-1-9Z",
  history: "M12 8v4l3 3M21 12a9 9 0 1 1-3-6.7M21 4v5h-5",
  settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.3.9a7 7 0 0 0-2-1.2L14 3h-4l-.6 2.5a7 7 0 0 0-2 1.2l-2.3-.9-2 3.4 2 1.6a7 7 0 0 0 0 2.4l-2 1.6 2 3.4 2.3-.9a7 7 0 0 0 2 1.2L10 21h4l.6-2.5a7 7 0 0 0 2-1.2l2.3.9 2-3.4-2-1.6c.07-.4.1-.8.1-1.2Z",
  help: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20ZM9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.8.4-1.3.9-1.3 1.7v.5M12 17h.01",
};

const NAV_ITEMS: { key: keyof typeof ICONS; label: string; href: string }[] = [
  { key: "agents", label: "Agents", href: "/" },
  { key: "templates", label: "Templates", href: "/" },
  { key: "datasets", label: "Datasets", href: "/flowchart" },
  { key: "integrations", label: "Integrations", href: "/" },
  { key: "history", label: "History", href: "/" },
  { key: "settings", label: "Settings", href: "/" },
  { key: "help", label: "Help", href: "/" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <Link href="/" className="sidebar-logo">
          <span className="sidebar-logo-mark">◈</span>
          <span className="sidebar-logo-text">Instant AI</span>
        </Link>

        <Link href="/" className="sidebar-create-btn">
          <span className="sidebar-create-icon">+</span>
          Create
        </Link>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.key}
              href={item.href}
              className={`sidebar-nav-item ${pathname === item.href && item.key === "agents" ? "is-active" : ""}`}
            >
              <Icon path={ICONS[item.key]} />
              {item.label}
            </Link>
          ))}
        </nav>
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-upgrade-card">
          <span className="sidebar-upgrade-title">Upgrade to Pro</span>
          <p className="sidebar-upgrade-copy">Unlock live AI mode, unlimited demos, and priority support.</p>
          <button type="button" className="sidebar-upgrade-btn">
            Upgrade
          </button>
        </div>

        <div className="sidebar-profile">
          <span className="sidebar-avatar">W</span>
          <div className="sidebar-profile-text">
            <span className="sidebar-profile-name">Winfomi Demo</span>
            <span className="sidebar-profile-role">Sandbox workspace</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
