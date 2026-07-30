import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import Lessons from "../src/pages/Lessons";

vi.mock("../src/api/client", () => ({
  api: vi.fn(async () => ({
    ok: true,
    json: async () => [
      {
        key: "sqli",
        title: "SQL Injection",
        vuln_class: "SQL Injection",
        owasp_web: "A03 Injection",
        owasp_api: "",
        has_probe: false,
        status: "completed",
      },
      {
        key: "missing-headers",
        title: "Missing Security Headers",
        vuln_class: "Security Misconfiguration",
        owasp_web: "A05 Security Misconfiguration",
        owasp_api: "",
        has_probe: true,
        status: "not_started",
      },
    ],
  })),
}));

describe("Lessons", () => {
  it("renders lesson cards with a completion badge for finished lessons", async () => {
    render(
      <MemoryRouter>
        <Lessons />
      </MemoryRouter>,
    );
    expect(await screen.findByText("SQL Injection")).toBeInTheDocument();
    expect(screen.getByText("Missing Security Headers")).toBeInTheDocument();
    // Exactly the completed lesson shows the badge.
    expect(screen.getByLabelText("completed")).toBeInTheDocument();
  });
});
