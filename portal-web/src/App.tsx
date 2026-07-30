import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading…</p>;
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/*" element={user ? <Dashboard /> : <Navigate to="/login" replace />} />
    </Routes>
  );
}
