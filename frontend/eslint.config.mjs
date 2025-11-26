import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // Disable setState in useEffect error - intentional in SSR hooks for initialization
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/exhaustive-deps": "off",
      "@typescript-eslint/no-unused-vars": ["warn", {
        "argsIgnorePattern": "^_",
        "varsIgnorePattern": "^_"
      }],
      // Suppress false positives - documented in sonar-project.properties
      "@typescript-eslint/no-deprecated": "off", // External library deprecations (Vercel AI SDK)
      "jsx-a11y/no-static-element-interactions": "off", // Modal backdrop patterns with stopPropagation
      "jsx-a11y/click-events-have-key-events": "off", // Non-interactive div onClick handlers
      "jsx-a11y/no-noninteractive-element-interactions": "off", // Drag-and-drop zones
      "jsx-a11y/interactive-supports-focus": "off", // role="button" with tabIndex is valid ARIA
    }
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Additional ignores:
    "coverage/**",
    "test/**",
    "*.config.*"
  ]),
]);

export default eslintConfig;
