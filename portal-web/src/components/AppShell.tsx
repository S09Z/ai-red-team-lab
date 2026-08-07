import { type ReactNode } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

// Nav item -> the feature whose read permission reveals it.
const NAV: { label: string; feature: string; to?: string }[] = [
  { label: "Lessons", feature: "lessons", to: "/lessons" },
  { label: "Tools", feature: "tools" },
  { label: "Docs", feature: "docs" },
  { label: "Reports", feature: "reports" },
  { label: "Admin", feature: "users", to: "/admin" },
];

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout, can } = useAuth();
  return (
    <div>
      <header>
        <strong>
          <Link to="/">Red Team Lab Portal</Link>
        </strong>
        <nav>
          {NAV.filter((item) => can(item.feature, "read")).map((item) => (
            <span key={item.label} style={{ marginLeft: 12 }}>
              {item.to ? <Link to={item.to}>{item.label}</Link> : item.label}
            </span>
          ))}
        </nav>
        <span>{user?.email}</span>
        <button onClick={() => void logout()}>Log out</button>
      </header>
      <main>{children}</main>
    </div>
  );
}
