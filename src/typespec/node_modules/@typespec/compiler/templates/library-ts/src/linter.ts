import { defineLinter } from "@typespec/compiler";
import { noInterfaceRule } from "./rules/no-interfaces.rule.js";

export const $linter = defineLinter({
  rules: [noInterfaceRule],
  ruleSets: {
    recommended: {
      enable: { [`{{name}}/${noInterfaceRule.name}`]: true },
    },
    all: {
      enable: { [`{{name}}/${noInterfaceRule.name}`]: true },
    },
  },
});
