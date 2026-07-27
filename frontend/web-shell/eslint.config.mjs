import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({
  baseDirectory: import.meta.dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    // `next-env.d.ts` is generated and maintained by Next.js itself (it
    // regenerates the file on every build, including the
    // `/// <reference path="./.next/types/routes.d.ts" />` line that
    // @typescript-eslint/triple-slash-reference rejects). It is excluded
    // from inspection here rather than edited, and rather than disabling
    // the rule: every handwritten .ts/.tsx file in this workspace stays
    // fully linted.
    ignores: ["node_modules/**", ".next/**", "dist/**", "next-env.d.ts"],
  },
];

export default eslintConfig;
