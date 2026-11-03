import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

interface RouteContext {
  params: Promise<{ path: string[] }>;
}

async function proxy(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const internalBase = process.env.API_INTERNAL_URL || "http://api:8000";
  const incoming = new URL(request.url);
  const target = new URL("/" + path.join("/") + incoming.search, internalBase);
  const headers = new Headers(request.headers);
  headers.delete("connection");
  headers.delete("content-length");
  headers.delete("host");
  headers.set("x-forwarded-host", incoming.host);
  headers.set("x-forwarded-proto", incoming.protocol.replace(":", ""));

  const method = request.method.toUpperCase();
  const body = method === "GET" || method === "HEAD"
    ? undefined
    : await request.arrayBuffer();
  const upstream = await fetch(target, {
    method,
    headers,
    body,
    cache: "no-store",
    redirect: "manual"
  });
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("connection");
  responseHeaders.delete("content-length");
  responseHeaders.delete("transfer-encoding");
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
