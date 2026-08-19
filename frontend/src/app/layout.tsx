import type { Metadata } from "next";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Instant AI Agent Sandbox",
  description: "Describe a business problem in plain English and get a working AI-agent prototype instantly.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <Sidebar />
          <div className="app-main">{children}</div>
        </div>
      </body>
    </html>
  );
}
