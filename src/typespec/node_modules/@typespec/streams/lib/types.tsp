namespace TypeSpec.Streams;

/**
 * Defines a model that represents a stream protocol type whose data is described
 * by `Type`.
 *
 * This can be useful when the underlying data type is not relevant, or to serve as
 * a base type for custom streams.
 *
 * @template Type The type of the stream's data.
 */
@doc("")
@streamOf(Type)
model Stream<Type> {}
