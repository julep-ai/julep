import { createTestHost, createTestWrapper } from "@typespec/compiler/testing";
import { LibraryTsTestLibrary } from "../src/testing/index.js";

export async function createLibraryTsTestHost() {
  return createTestHost({
    libraries: [LibraryTsTestLibrary],
  });
}

export async function createLibraryTsTestRunner() {
  const host = await createLibraryTsTestHost();

  return createTestWrapper(host, {
    autoUsings: ["LibraryTs"]
  });
}

