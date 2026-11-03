export interface BrowserSession {
  authenticated: boolean;
  csrf_token: string;
  identity?: {
    issuer: string;
    subject: string;
    email: string;
    name: string;
    is_admin: boolean;
  };
}

export async function loadAuthSession(): Promise<BrowserSession | null> {
  const response = await fetch("/api/auth/session", {
    cache: "no-store",
    credentials: "include"
  });
  if (!response.ok) return null;
  const session = await response.json() as BrowserSession;
  return session.authenticated ? session : null;
}

export function beginLogin(): void {
  window.location.assign("/api/auth/login");
}

export async function endSession(csrfToken: string): Promise<void> {
  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": csrfToken }
  });
}
