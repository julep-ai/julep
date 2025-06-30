import "../dist/src/decorators.js";

using TypeSpec.Reflection;

namespace LibraryTs;

/**
 * __Example Decorator__
 * Provide an alternate name for an operation.
 * @param name The alternate name.
 */
extern dec alternateName(target: Operation, name: valueof string);
