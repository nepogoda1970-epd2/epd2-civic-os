import { NextResponse, type NextRequest } from "next/server";

/**
 * Content Security Policy with a per-request nonce.
 *
 * The App Router emits inline bootstrap scripts, and a policy of
 * `script-src 'self'` blocks them, which breaks the page. The wrong fix is
 * `'unsafe-inline'`: it would weaken the boundary for every script on an origin
 * that renders confidential case material in order to admit one framework
 * script. The right fix is a fresh nonce per response, which Next applies to
 * its own inline scripts and which no injected script can guess.
 *
 * The policy is set here rather than in `next.config.ts` so that the nonce is
 * genuinely per-request. The remaining, nonce-free headers stay in the config.
 */
function nonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes));
}

export function middleware(request: NextRequest) {
  const value = nonce();
  const policy = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${value}' 'strict-dynamic'`,
    "style-src 'self'",
    "img-src 'self' data:",
    "font-src 'self'",
    // No telemetry platform is connected and no third-party origin is
    // reachable. 'self' is wider than this workspace currently needs and is
    // kept only so the framework's own navigation payloads load.
    "connect-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "frame-src 'none'",
    "base-uri 'none'",
    "object-src 'none'",
    "worker-src 'none'",
    "manifest-src 'none'",
    "upgrade-insecure-requests",
  ].join("; ");

  const headers = new Headers(request.headers);
  headers.set("x-nonce", value);
  headers.set("content-security-policy", policy);

  const response = NextResponse.next({ request: { headers } });
  response.headers.set("content-security-policy", policy);
  return response;
}

export const config = {
  matcher: [
    // Every document request. Static assets carry the config headers only.
    {
      source: "/((?!_next/static|_next/image|favicon.ico).*)",
      missing: [
        // Prefetches and in-app navigation payloads are not documents: they
        // carry no <head> and need no nonce. Minting one for them would also
        // change the policy mid-navigation, which the router answers with a
        // full page load — and a full page load discards an unsaved draft that
        // this workspace cannot persist anywhere.
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
        { type: "header", key: "rsc" },
      ],
    },
  ],
};
