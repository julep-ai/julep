import { strictEqual } from "node:assert";
import { describe, it, beforeEach } from "node:test";
import { Operation } from "@typespec/compiler";
import { BasicTestRunner, expectDiagnostics, extractCursor } from "@typespec/compiler/testing";
import { getAlternateName } from "../src/decorators.js";
import { createLibraryTsTestRunner } from "./test-host.js";

describe("decorators", () => {
  let runner: BasicTestRunner;

  beforeEach(async () => {
    runner = await createLibraryTsTestRunner();
  })

  describe("@alternateName", () => {
    it("set alternate name on operation", async () => {
      const { test } = (await runner.compile(
        `@alternateName("bar") @test op test(): void;`
      )) as { test: Operation };
      strictEqual(getAlternateName(runner.program, test), "bar");
    });

    it("emit diagnostic if not used on an operation", async () => {
      const diagnostics = await runner.diagnose(
        `@alternateName("bar") model Test {}`
      );
      expectDiagnostics(diagnostics, {
        severity: "error",
        code: "decorator-wrong-target",
        message: "Cannot apply @alternateName decorator to Test since it is not assignable to Operation"
      })
    });


    it("emit diagnostic if using banned name", async () => {
      const {pos, source} = extractCursor(`@alternateName(┆"banned") op test(): void;`)
      const diagnostics = await runner.diagnose(
        source
      );
      expectDiagnostics(diagnostics, {
        severity: "error",
        code: "library-ts/banned-alternate-name",
        message: `Banned alternate name "banned".`,
        pos: pos + runner.autoCodeOffset
      })
    });
  });
});
