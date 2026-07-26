// Lab target client-side script — intentionally insecure for training purposes.

const API_BASE = "http://localhost:5000";
// DEV_TOKEN = "dev-abc123"  // TODO: remove before prod

// Fetch all users on page load (sensitive data exposure via unauthenticated API).
fetch(`${API_BASE}/api/users`)
    .then(r => r.json())
    .then(users => console.log("users loaded", users.length));

function storeSession(token) {
    // INSECURE: token stored in localStorage, accessible to any JS on the page.
    localStorage.setItem("session_token", token);
}

function getSession() {
    return localStorage.getItem("session_token");
}
