/**
 * The module that replaces the governed test runtime in a production build.
 *
 * `next.config.ts` rewrites every request for `governedTestRuntime` to this
 * file unless the governed test flag is exactly `"1"`, so the fixture module is
 * not merely unreachable in production — it is absent from the output. A
 * browser gate proves that by scanning the built bundle for the fixture marker.
 *
 * If the dynamic import is nonetheless reached, this throws rather than
 * degrading to something usable. A fixture that silently activates in a
 * mandate-scoped workspace would present fabricated citizen cases as real, and
 * that is the failure this arrangement exists to prevent.
 */

import type { RepresentativeRuntime } from "./ports";

export const FIXTURE_ABSENT = true as const;

export function createGovernedTestRuntime(): RepresentativeRuntime {
  throw new Error(
    "WS04_FIXTURE_ABSENT_IN_PRODUCTION: the governed test runtime is not part of this build",
  );
}
