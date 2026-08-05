import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { refresh } = useAuth();

  async function stubLogin() {
    await api("/auth/stub", { method: "POST" });
    await refresh();
  }

  return (
    <main>
      <h1>AI Red Team Lab — Portal</h1>
      <p>Sign in to run guided lessons, launch the observation tools, and build reports.</p>
      <button onClick={stubLogin}>Dev login (stub)</button>
      <p>
        <a href="/auth/github/login">Sign in with GitHub</a>
        {" · "}
        <a href="/auth/google/login">Sign in with Google</a>
      </p>
    </main>
  );
}
