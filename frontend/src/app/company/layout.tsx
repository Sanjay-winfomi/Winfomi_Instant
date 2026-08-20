"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import CompanySidebar from "@/components/CompanySidebar";
import { clearCompanyToken, getCompanyToken, me } from "@/services/companyApi";
import "./company.css";

export default function CompanyLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/company/login";
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (isLoginPage) return;
    const token = getCompanyToken();
    if (!token) {
      router.replace("/company/login");
      return;
    }
    me()
      .then(() => setChecked(true))
      .catch(() => {
        clearCompanyToken();
        router.replace("/company/login");
      });
  }, [isLoginPage, router]);

  if (isLoginPage) return <>{children}</>;
  if (!checked) return null;

  return (
    <div className="app-shell">
      <CompanySidebar />
      <div className="app-main">
        <div className="app-main-content">{children}</div>
      </div>
    </div>
  );
}
