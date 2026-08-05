import { type ReactNode } from "react";

import { useAuth } from "../auth/AuthContext";

const NAV = ["Lessons", "Tools", "Docs", "Reports"];

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div>
      <header>
        <strong>Red Team Lab Portal</strong>
        <nav>
          {NAV.map((item) => (
            <span key={item} style={{ marginLeft: 12, opacity: 0.6 }}>
              {item}
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
