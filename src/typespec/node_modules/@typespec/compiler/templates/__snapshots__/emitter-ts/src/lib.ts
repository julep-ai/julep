import { createTypeSpecLibrary } from "@typespec/compiler";

export const $lib = createTypeSpecLibrary({
  name: "emitter-ts",
  diagnostics: {},
});

export const { reportDiagnostic, createDiagnostic } = $lib;
