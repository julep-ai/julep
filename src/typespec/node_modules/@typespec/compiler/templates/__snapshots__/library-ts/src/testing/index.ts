import { resolvePath } from "@typespec/compiler";
import { createTestLibrary, TypeSpecTestLibrary } from "@typespec/compiler/testing";
import { fileURLToPath } from "url";

export const LibraryTsTestLibrary: TypeSpecTestLibrary = createTestLibrary({
  name: "library-ts",
  packageRoot: resolvePath(fileURLToPath(import.meta.url), "../../../../"),
});
