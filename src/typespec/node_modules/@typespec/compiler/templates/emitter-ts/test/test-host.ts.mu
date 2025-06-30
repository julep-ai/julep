import { Diagnostic, resolvePath } from "@typespec/compiler";
import {
  createTestHost,
  createTestWrapper,
  expectDiagnosticEmpty,
} from "@typespec/compiler/testing";
import { {{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestLibrary } from "../src/testing/index.js";

export async function create{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestHost() {
  return createTestHost({
    libraries: [{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestLibrary],
  });
}

export async function create{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestRunner() {
  const host = await create{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestHost();

  return createTestWrapper(host, {
    compilerOptions: {
      noEmit: false,
      emit: ["{{name}}"],
    },
  });
}

export async function emitWithDiagnostics(
  code: string
): Promise<[Record<string, string>, readonly Diagnostic[]]> {
  const runner = await create{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestRunner();
  await runner.compileAndDiagnose(code, {
    outputDir: "tsp-output",
  });
  const emitterOutputDir = "./tsp-output/{{name}}";
  const files = await runner.program.host.readDir(emitterOutputDir);

  const result: Record<string, string> = {};
  for (const file of files) {
    result[file] = (await runner.program.host.readFile(resolvePath(emitterOutputDir, file))).text;
  }
  return [result, runner.program.diagnostics];
}

export async function emit(code: string): Promise<Record<string, string>> {
  const [result, diagnostics] = await emitWithDiagnostics(code);
  expectDiagnosticEmpty(diagnostics);
  return result;
}
