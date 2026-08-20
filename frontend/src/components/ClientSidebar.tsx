"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { getClientEmail } from "@/services/clientApi";
import "./Sidebar.css";

function Icon({ path }: { path: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={path} />
    </svg>
  );
}

const ICONS = {
  demos: "M4 6c0-1.1 3.58-2 8-2s8 .9 8 2-3.58 2-8 2-8-.9-8-2Zm0 0v12c0 1.1 3.58 2 8 2s8-.9 8-2V6M4 12c0 1.1 3.58 2 8 2s8-.9 8-2",
  help: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20ZM9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.8.4-1.3.9-1.3 1.7v.5M12 17h.01",
};

export default function ClientSidebar() {
  const pathname = usePathname();
  const email = typeof window !== "undefined" ? getClientEmail() : null;

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <Link href="/" className="sidebar-logo">
          <span className="sidebar-logo-mark">◈</span>
          <span className="sidebar-logo-text">
            WINFOMI
            <br />
            Instant AI
          </span>
        </Link>

        <Link href="/create" className="sidebar-create-btn">
          <span className="sidebar-create-icon">+</span>
          Create Demo
        </Link>

        <nav className="sidebar-nav">
          <Link href="/demos" className={`sidebar-nav-item ${pathname?.startsWith("/demos") || pathname?.startsWith("/demo/") ? "is-active" : ""}`}>
            <Icon path={ICONS.demos} />
            My Demo
          </Link>
          <Link href="/help" className={`sidebar-nav-item ${pathname === "/help" ? "is-active" : ""}`}>
            <Icon path={ICONS.help} />
            Help
          </Link>
        </nav>
      </div>

      <div className="sidebar-bottom">
        {email && (
          <div className="sidebar-profile">
            <span className="sidebar-avatar">{email[0]?.toUpperCase()}</span>
            <div className="sidebar-profile-text">
              <span className="sidebar-profile-name">{email}</span>
              <span className="sidebar-profile-role">Client workspace</span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
