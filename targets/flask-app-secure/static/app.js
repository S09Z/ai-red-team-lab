// Hardened lab target client script.
//
// Contrast with the vulnerable app's app.js: no hardcoded API base, no
// dev-token comment, and no session token in localStorage. Session state is
// carried by the HttpOnly, Secure, SameSite session cookie the server sets,
// which JavaScript deliberately cannot read.

// Same-origin fetch; the browser attaches the session cookie automatically.
async function loadUsers() {
  const res = await fetch("/api/users", { credentials: "same-origin" });
  if (!res.ok) return [];
  return res.json();
}
