import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Admin from "../src/pages/Admin";

// Hoisted so the vi.mock factory can read it; flipped per test.
const state = vi.hoisted(() => ({ can: false }));

vi.mock("../src/auth/AuthContext", () => ({
  useAuth: () => ({ can: () => state.can, refresh: vi.fn() }),
}));

vi.mock("../src/api/client", () => ({
  api: vi.fn(async () => ({ ok: true, json: async () => [] })),
}));

describe("Admin", () => {
  it("hides administration without users:read", () => {
    state.can = false;
    render(<Admin />);
    expect(screen.getByText(/do not have access/i)).toBeInTheDocument();
  });

  it("renders the admin surface when permitted", () => {
    state.can = true;
    render(<Admin />);
    expect(screen.getByRole("heading", { name: /administration/i })).toBeInTheDocument();
  });
});
