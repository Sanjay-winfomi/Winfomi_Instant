"use client";

import ClientSidebar from "@/components/ClientSidebar";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <ClientSidebar />
      <div className="app-main">
        <div className="app-main-content">{children}</div>
      </div>
    </div>
  );
}
