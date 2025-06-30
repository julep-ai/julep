import { resolvePath } from "@typespec/compiler";
import { createTestLibrary, TypeSpecTestLibrary } from "@typespec/compiler/testing";
import { fileURLToPath } from "url";

export const EmitterTsTestLibrary: TypeSpecTestLibrary = createTestLibrary({
  name: "emitter-ts",
  packageRoot: resolvePath(fileURLToPath(import.meta.url), "../../../../"),
});
