import type { ReactNode } from "react";
import "./TopBar.css";

interface Props {
  left?: ReactNode;
}

export default function TopBar({ left }: Props) {
  return (
    <header className="topbar">
      <div className="topbar-left">{left}</div>
      <div className="topbar-right">
        <button type="button" className="topbar-icon-btn" aria-label="Search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3-3" />
          </svg>
        </button>
        <button type="button" className="topbar-icon-btn" aria-label="Notifications">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.7 21a2 2 0 0 1-3.4 0" />
          </svg>
        </button>
        <span className="topbar-avatar">W</span>
      </div>
    </header>
  );
}
