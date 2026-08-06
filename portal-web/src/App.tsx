import { Navigate, Route, Routes } from "react-router-dom";

import AppShell from "./components/AppShell";
import { useAuth } from "./auth/AuthContext";
import Admin from "./pages/Admin";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading…</p>;
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      {user ? (
        <>
          <Route
            path="/admin"
            element={
              <AppShell>
                <Admin />
              </AppShell>
            }
          />
          <Route path="/*" element={<Dashboard />} />
        </>
      ) : (
        <Route path="/*" element={<Navigate to="/login" replace />} />
      )}
    </Routes>
  );
}
