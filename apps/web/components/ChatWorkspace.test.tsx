import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
      if (url.endsWith("/v1/projects")) {
        return jsonResponse({
          items: [{
            id: "p1",
            name: "Akkar potatoes",
            instructions: "Use project field notes.",
            created_at: "",
            updated_at: ""
          }]
        });
      }
      if (url.endsWith("/v1/artifacts")) {
        return jsonResponse({
          items: [{
            id: "a1",
            project_id: "p1",
            artifact_type: "farm_action_plan",
            filename: "action-plan.docx",
            mime_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            created_at: ""
          }]
        });
      }
      if (url.endsWith("/v1/projects/p1/documents")) {
        return jsonResponse({
          items: [{
            id: "d1",
            project_id: "p1",
            filename: "field-notes.txt",
            mime_type: "text/plain",
            size_bytes: 1024,
            created_at: ""
          }]
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

describe("ChatWorkspace retained project workflows", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("shows projects, documents, artifacts, and export in the canonical UI", async () => {
    stubBackend();
    render(<ChatWorkspace />);

    await screen.findByText("Answer text");
    fireEvent.click(screen.getByRole("button", { name: "EN" }));
    fireEvent.click(await screen.findByRole("button", { name: "Projects and files" }));

    expect(await screen.findByRole("dialog", { name: "Projects and files" })).toBeInTheDocument();
    expect((await screen.findAllByText("Akkar potatoes")).length).toBeGreaterThan(0);
    expect(await screen.findByText("field-notes.txt")).toBeInTheDocument();
    expect(await screen.findByText("action-plan.docx")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Export my data/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start project chat/ })).toBeInTheDocument();
  });
});

describe("ChatWorkspace interrupted stream recovery", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("hydrates a completed persisted turn when SSE closes without a terminal event", async () => {
    const persisted = {
      ...assistantMessage,
      id: "recovered-m1",
      content: "Recovered answer"
    };
    let turnStarted = false;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/v1/config")) {
        return jsonResponse({
          app_name: "RAISE",
          agreement_version: "v1",
          default_language: "en",
          modes: [
            { id: "standard", label_en: "Standard", label_ar: "Standard", description: "" }
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
        return jsonResponse({ items: turnStarted ? [persisted] : [] });
      }
      if (url.endsWith("/v1/usage")) {
        return jsonResponse({
          weekly_spend_usd: 0,
          weekly_limit_usd: 7,
          week_start: "",
          week_end: ""
        });
      }
      if (url.endsWith("/v1/turns") && init?.method === "POST") {
        turnStarted = true;
        const stream = [
          "event: status\n",
          "data: " + JSON.stringify({ stage: "generation", turn_id: "t-recover" }) + "\n\n",
          "event: content.delta\n",
          "data: " + JSON.stringify({ text: "Partial", turn_id: "t-recover" }) + "\n\n"
        ].join("");
        return new Response(stream, { status: 200 });
      }
      if (url.endsWith("/v1/turns/t-recover")) {
        return jsonResponse({
          turn_id: "t-recover",
          request_id: "request-1",
          status: "complete",
          terminal: true,
          message: persisted,
          error: null
        });
      }
      throw new Error("Unexpected fetch: " + url);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<ChatWorkspace />);

    const composer = (await screen.findAllByRole("textbox"))
      .find((element) => element.tagName === "TEXTAREA");
    if (!composer) throw new Error("Composer was not rendered");
    fireEvent.change(composer, { target: { value: "Question" } });
    const send = document.querySelector<HTMLButtonElement>("button.send-button");
    if (!send) throw new Error("Send button was not rendered");
    await waitFor(() => expect(send).not.toBeDisabled());
    fireEvent.click(send);

    expect(await screen.findByText("Recovered answer")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([input]) =>
      String(input).endsWith("/v1/turns/t-recover")
    )).toBe(true);
    expect(screen.queryByText("Partial")).not.toBeInTheDocument();
  });
});
