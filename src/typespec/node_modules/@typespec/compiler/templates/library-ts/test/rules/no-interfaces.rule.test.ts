import {
  LinterRuleTester,
  createLinterRuleTester,
  createTestRunner,
} from "@typespec/compiler/testing";
import { beforeEach, describe, it } from "node:test";
import { noInterfaceRule } from "../../src/rules/no-interfaces.rule.js";

describe("noInterfaceRule", () => {
  let ruleTester: LinterRuleTester;

  beforeEach(async () => {
    const runner = await createTestRunner();
    ruleTester = createLinterRuleTester(runner, noInterfaceRule, "{{name}}");
  });

  describe("models", () => {
    it("emit diagnostics if using interfaces", async () => {
      await ruleTester.expect(`interface Test {}`).toEmitDiagnostics({
        code: "{{name}}/no-interface",
        message: "Interface shouldn't be used with this library. Keep operations at the root.",
      });
    });

    it("should be valid if operation is at the root", async () => {
      await ruleTester.expect(`op test(): void;`).toBeValid();
    });
  });
});
