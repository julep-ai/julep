import "../dist/src/private.decorators.js";

/**
 * Private decorators. Those are meant for internal use inside Http types only.
 */
namespace TypeSpec.Http.Private;

extern dec plainData(target: TypeSpec.Reflection.Model);
extern dec httpFile(target: TypeSpec.Reflection.Model);
extern dec httpPart(
  target: TypeSpec.Reflection.Model,
  type: unknown,
  options: valueof HttpPartOptions
);
