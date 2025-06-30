import { createTypeSpecLibrary } from "@typespec/compiler";

export const $lib = createTypeSpecLibrary({
  name: "{{name}}",
  diagnostics: {},
});

export const { reportDiagnostic, createDiagnostic } = $lib;
