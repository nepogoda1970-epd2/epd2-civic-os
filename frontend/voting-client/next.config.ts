import path from "node:path";

import type { NextConfig } from "next";

/**
 * WS-03 deployment profile.
 *
 * The headers below are the browser-boundary half of the isolation the stage
 * contract requires.  They are asserted by tests/browser/front04.browser.spec.ts
 * against a running production build, not merely declared here.
 *
 * The Content-Security-Policy is NOT here: it carries a per-request nonce and
 * is therefore set in `middleware.ts`. Setting it in both places would give the
 * browser two policies to intersect, and the stricter nonce-free one would
 * block the framework's own inline bootstrap.
 *
 * `Clear-Site-Data` is deliberately absent: it would be the right instrument at
 * the end of a completed journey, and no completed journey exists while the
 * casting runtime is blocked. Adding it now would imply a terminal state the
 * client cannot reach.
 */
const SECURITY_HEADERS = [
  { key: "Cache-Control", value: "no-store" },
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  {
    key: "Permissions-Policy",
    value: [
      "camera=()",
      "microphone=()",
      "geolocation=()",
      "interest-cohort=()",
      "browsing-topics=()",
      "payment=()",
      "usb=()",
    ].join(", "),
  },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
  { key: "Cross-Origin-Embedder-Policy", value: "require-corp" },
];

/**
 * Fixture elimination.
 *
 * Unless the governed test flag is exactly "1", every request for the governed
 * test runtime is rewritten to `runtime/fixtureAbsent.ts`, so the fixture
 * module — and the fixture marker string a gate searches for — is absent from
 * the emitted bundle rather than merely unreachable inside it.
 */
const GOVERNED_TEST_ENABLED =
  process.env.NEXT_PUBLIC_FRONT04_GOVERNED_TEST === "1";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  productionBrowserSourceMaps: false,
  // The Voting Client ships no images, so the framework's image-optimisation
  // endpoint is pure attack surface on this origin — and it is backed by sharp,
  // which carries inherited libvips advisories. Disabling the optimiser removes
  // the endpoint's processing path rather than leaving it unused but reachable.
  // Found by the dependency-reachability analysis, not by review.
  images: { unoptimized: true },
  webpack(config, { webpack }) {
    if (!GOVERNED_TEST_ENABLED) {
      config.plugins.push(
        new webpack.NormalModuleReplacementPlugin(
          /runtime[\\/]governedTestRuntime/,
          path.resolve(import.meta.dirname, "runtime/fixtureAbsent.ts"),
        ),
      );
    }
    return config;
  },
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
};

export default nextConfig;
