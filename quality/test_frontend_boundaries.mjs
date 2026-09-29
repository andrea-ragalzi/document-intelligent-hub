import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import test from "node:test";

const { ESLint } = createRequire(new URL("../frontend/package.json", import.meta.url))("eslint");

const eslint = new ESLint({ cwd: fileURLToPath(new URL("../frontend", import.meta.url)) });

for (const [filePath, dependency, forbidden] of [
  ["hooks/useExample.ts", "@/components/Sidebar", true],
  ["hooks/queries/useExample.ts", "../../components/Sidebar", true],
  ["stores/example.ts", "@/app/api/chat/route", true],
  ["app/api/example/route.ts", "../../../hooks/useDocuments", true],
  ["components/Example.tsx", "../app/api/chat/route", true],
  ["hooks/useExample.ts", "@/lib/documentApi", false],
  ["stores/example.ts", "@/lib/types", false],
  ["app/api/example/route.ts", "@/lib/constants", false],
]) {
  test(`${filePath} ${forbidden ? "rejects" : "allows"} ${dependency}`, async () => {
    const [result] = await eslint.lintText(`export * from "${dependency}";`, { filePath });
    assert.equal(result.messages.some(message => message.fatal), false);
    assert.equal(
      result.messages.some(message => message.ruleId === "no-restricted-imports"),
      forbidden
    );
  });
}
