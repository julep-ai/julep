import { createRule } from "@typespec/compiler";

export const noInterfaceRule = createRule({
  name: "no-interface",
  severity: "warning",
  description: "Make sure interface are not used.",
  messages: {
    default: "Interface shouldn't be used with this library. Keep operations at the root.",
  },
  create: (context) => {
    return {
      interface: (iface) => {
        context.reportDiagnostic({
          target: iface,
        });
      },
    };
  },
});
