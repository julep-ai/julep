import { Diagnostic, resolvePath } from "@typespec/compiler";
import {
  createTestHost,
  createTestWrapper,
  expectDiagnosticEmpty,
} from "@typespec/compiler/testing";
import { EmitterTsTestLibrary } from "../src/testing/index.js";

export async function createEmitterTsTestHost() {
  return createTestHost({
    libraries: [EmitterTsTestLibrary],
  });
}

export async function createEmitterTsTestRunner() {
  const host = await createEmitterTsTestHost();

  return createTestWrapper(host, {
    compilerOptions: {
      noEmit: false,
      emit: ["emitter-ts"],
    },
  });
}

export async function emitWithDiagnostics(
  code: string
): Promise<[Record<string, string>, readonly Diagnostic[]]> {
  const runner = await createEmitterTsTestRunner();
  await runner.compileAndDiagnose(code, {
    outputDir: "tsp-output",
  });
  const emitterOutputDir = "./tsp-output/emitter-ts";
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
