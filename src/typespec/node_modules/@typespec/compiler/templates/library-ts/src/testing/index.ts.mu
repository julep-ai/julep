import { resolvePath } from "@typespec/compiler";
import { createTestLibrary, TypeSpecTestLibrary } from "@typespec/compiler/testing";
import { fileURLToPath } from "url";

export const {{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestLibrary: TypeSpecTestLibrary = createTestLibrary({
  name: "{{name}}",
  packageRoot: resolvePath(fileURLToPath(import.meta.url), "../../../../"),
});
