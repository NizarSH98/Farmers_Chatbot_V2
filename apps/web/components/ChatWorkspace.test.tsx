import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChatWorkspace } from "./ChatWorkspace";

vi.mock("@/lib/supabase", () => ({
  supabaseBrowser: () => ({
    auth: {
      getSession: () =>
        Promise.resolve({ data: { session: { access_token: "test-token" } } }),
      onAuthStateChange: () => ({
        data: { subscription: { unsubscribe: () => {} } }
      }),
      signOut: () => Promise.resolve({ error: null })
    }
  })
}));

const assistantMessage = {
  id: "m1",
  role: "assistant",
  content: "Answer text",
  status: "complete",
  citations: [],
  tools: [],
  attachments: [],
  created_at: new Date().toISOString()
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

function stubBackend(feedbackStatus = 201) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/v1/config")) {
        return jsonResponse({
          app_name: "RAISE",
          agreement_version: "v1",
          default_language: "en",
          modes: [
            { id: "standard", label_en: "Standard", label_ar: "متوازن", description: "" }
          ],
          models: [{ id: "m", label: "M", description: "", supports_images: false }]
        });
      }
      if (url.endsWith("/v1/me")) {
        return jsonResponse({
          id: "u1",
          name: "Test",
          email: "t@test.dev",
          role: "user",
          consent_current: true,
          default_mode: "standard"
        });
      }
      if (url.endsWith("/v1/conversations")) {
        return jsonResponse({
          items: [{ id: "c1", title: "Chat", archived: false, created_at: "", updated_at: "" }]
        });
      }
      if (url.includes("/v1/conversations/c1/messages")) {
        return jsonResponse({ items: [assistantMessage] });
      }
      if (url.endsWith("/v1/usage")) {
        return jsonResponse({
          weekly_spend_usd: 1.5,
          weekly_limit_usd: 7,
          week_start: "",
          week_end: ""
        });
      }
      if (url.endsWith("/v1/feedback")) {
        return feedbackStatus >= 400
          ? jsonResponse({ detail: "boom" }, feedbackStatus)
          : jsonResponse({ id: 1 }, feedbackStatus);
      }
      throw new Error("Unexpected fetch: " + url);
    })
  );
}

describe("ChatWorkspace feedback buttons", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("marks the clicked button as pressed and lets the user switch their vote", async () => {
    stubBackend();
    render(<ChatWorkspace />);

    await screen.findByText("Answer text");
    const helpful = screen.getByRole("button", { name: "مفيد" });
    const notHelpful = screen.getByRole("button", { name: "غير مفيد" });
    expect(helpful).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(helpful);
    expect(await screen.findByRole("button", { name: "مفيد", pressed: true })).toBeInTheDocument();
    expect(helpful.className).toContain("feedback-active");
    expect(notHelpful).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(notHelpful);
    expect(await screen.findByRole("button", { name: "غير مفيد", pressed: true })).toBeInTheDocument();
    expect(helpful).toHaveAttribute("aria-pressed", "false");
    expect(helpful.className).not.toContain("feedback-active");
  });

  it("reverts the pressed state and surfaces an error when the request fails", async () => {
    stubBackend(500);
    render(<ChatWorkspace />);

    await screen.findByText("Answer text");
    const helpful = screen.getByRole("button", { name: "مفيد" });

    fireEvent.click(helpful);
    await screen.findByRole("alert");
    expect(helpful).toHaveAttribute("aria-pressed", "false");
  });
});

describe("ChatWorkspace weekly usage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("shows the fetched weekly spend and limit in settings", async () => {
    stubBackend();
    render(<ChatWorkspace />);

    await screen.findByText("Answer text");
    fireEvent.click(screen.getByRole("button", { name: "الإعدادات" }));

    expect(await screen.findByText("$1.50 / $7.00")).toBeInTheDocument();
  });
});
