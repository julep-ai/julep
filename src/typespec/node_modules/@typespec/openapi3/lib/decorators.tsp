import "../dist/src/tsp-index.js";

namespace TypeSpec.OpenAPI;

using TypeSpec.Reflection;

/**
 * Specify that `oneOf` should be used instead of `anyOf` for that union.
 */
extern dec oneOf(target: Union | ModelProperty);
/**
 * Specify an external reference that should be used inside of emitting this type.
 * @param ref External reference(e.g. "../../common.json#/components/schemas/Foo")
 */
extern dec useRef(target: Model | ModelProperty, ref: valueof string);
