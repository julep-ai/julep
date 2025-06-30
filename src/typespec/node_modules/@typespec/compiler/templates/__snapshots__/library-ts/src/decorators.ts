import { DecoratorContext, Operation, Program } from "@typespec/compiler";
import { StateKeys, reportDiagnostic } from "./lib.js";

export const namespace = "LibraryTs";

/**
 * __Example implementation of the `@alternateName` decorator.__
 *
 * @param context Decorator context.
 * @param target Decorator target. Must be an operation.
 * @param name Alternate name.
 */
export function $alternateName(context: DecoratorContext, target: Operation, name: string) {
  if (name === "banned") {
    reportDiagnostic(context.program, {
      code: "banned-alternate-name",
      target: context.getArgumentTarget(0)!,
      format: { name },
    });
  }
  context.program.stateMap(StateKeys.alternateName).set(target, name);
}

/**
 * __Example accessor for  the `@alternateName` decorator.__
 *
 * @param program TypeSpec program.
 * @param target Decorator target. Must be an operation.
 * @returns Altenate name if provided on the given operation or undefined
 */
export function getAlternateName(program: Program, target: Operation): string | undefined {
  return program.stateMap(StateKeys.alternateName).get(target);
}
