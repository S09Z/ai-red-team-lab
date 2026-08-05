import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Login from "../src/pages/Login";

// The login page only needs `refresh` from the auth context.
vi.mock("../src/auth/AuthContext", () => ({
  useAuth: () => ({ refresh: vi.fn() }),
}));

describe("Login", () => {
  it("renders the stub dev-login button", () => {
    render(<Login />);
    expect(screen.getByRole("button", { name: /dev login/i })).toBeInTheDocument();
  });

  it("offers GitHub and Google sign-in links", () => {
    render(<Login />);
    expect(screen.getByRole("link", { name: /github/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /google/i })).toBeInTheDocument();
  });
});
