import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Winfomi Instant AI",
  description: "Describe your business problem and experience a working AI solution instantly.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
