/**
 * Runtime composition.
 *
 * The production build resolves to the production adapter and nothing else.
 * The governed test runtime is reached only through a dynamic import behind a
 * comparison against a build-time constant, so when the flag is not `"1"` the
 * bundler removes the branch and the fixture module is absent from the output.
 * A browser test asserts that absence by scanning the build for the fixture
 * marker, which is the mechanical form of "fixtures cannot activate".
 */

import { createProductionRuntime } from "./productionRuntime";
import type { VotingRuntime } from "./ports";

/**
 * Next inlines `process.env.NEXT_PUBLIC_*` at build time, so this comparison is
 * a literal comparison in the emitted bundle.
 */
export const GOVERNED_TEST_FLAG = process.env.NEXT_PUBLIC_FRONT04_GOVERNED_TEST;

export function governedTestProfileEnabled(): boolean {
  return GOVERNED_TEST_FLAG === "1";
}

export async function resolveVotingRuntime(): Promise<VotingRuntime> {
  if (process.env.NEXT_PUBLIC_FRONT04_GOVERNED_TEST === "1") {
    const governed = await import("./governedTestRuntime");
    return governed.createGovernedTestRuntime();
  }
  return createProductionRuntime();
}

/** The profile label the interface shows, so the state is never ambiguous. */
export function profileLabel(): string {
  return governedTestProfileEnabled()
    ? "Geprüftes Testprofil — keine echte Abstimmung"
    : "Produktionsprofil — keine freigegebene Laufzeit";
}
