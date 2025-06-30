import { createTestHost, createTestWrapper } from "@typespec/compiler/testing";
import { {{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestLibrary } from "../src/testing/index.js";

export async function create{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestHost() {
  return createTestHost({
    libraries: [{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestLibrary],
  });
}

export async function create{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestRunner() {
  const host = await create{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}TestHost();

  return createTestWrapper(host, {
    autoUsings: ["{{#casing.pascalCase}}{{name}}{{/casing.pascalCase}}"]
  });
}

