/**
 * The module that replaces the governed test runtime in a production build.
 *
 * `next.config.ts` rewrites every request for `governedTestRuntime` to this
 * file unless the governed test flag is exactly `"1"`, so the fixture module is
 * not merely unreachable in production — it is not in the output at all.  A
 * browser gate proves that by scanning the built bundle for the fixture marker.
 *
 * If the dynamic import is nonetheless reached, this throws rather than
 * degrading to something usable.  A fixture that silently activates is the
 * failure this whole arrangement exists to prevent.
 */

import type { VotingRuntime } from "./ports";

export const FIXTURE_ABSENT = true as const;

export function createGovernedTestRuntime(): VotingRuntime {
  throw new Error(
    "WS03_FIXTURE_ABSENT_IN_PRODUCTION: the governed test runtime is not part of this build",
  );
}
