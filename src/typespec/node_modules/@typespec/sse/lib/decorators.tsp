using TypeSpec.Reflection;

namespace TypeSpec.SSE;

/**
 * Indicates that the presence of this event is a terminal event,
 * and the client should disconnect from the server.
 */
extern dec terminalEvent(target: UnionVariant);
