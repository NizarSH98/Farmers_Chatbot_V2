import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

// Registry code vendored from shadcn/ui and assistant-ui. It is kept close to
// upstream so it can be re-pulled; the React Compiler advisory rules below
// stay fully enforced for our own code in components/raise and lib.
const VENDORED = [
  "components/ui/**",
  "components/assistant-ui/**",
  "components/*.tsx",
  "components/*.ts",
  "hooks/**"
];

export default defineConfig([
  ...nextVitals,
  ...nextTypescript,
  {
    files: VENDORED,
    rules: {
      "react-hooks/refs": "off",
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "react/no-unescaped-entities": "off",
      "@next/next/no-img-element": "off",
      "jsx-a11y/alt-text": "off"
    }
  },
  globalIgnores([".next/**", "coverage/**", "next-env.d.ts"])
]);
