import "@typespec/streams";
import "../http.tsp";

using TypeSpec.Streams;

namespace TypeSpec.Http.Streams;

/**
 * Defines a model that represents a stream protocol type whose data is described
 * by `Type`.
 *
 * The `ContentType` and `BodyType` describe how the stream is encoded over the wire,
 * while `Type` describes the data that the stream contains.
 *
 * @template Type The type of the stream's data.
 * @template ContentType The content type of the stream.
 * @template BodyType The underlying wire type of the stream.
 */
@doc("")
model HttpStream<Type, ContentType extends valueof string, BodyType extends bytes | string = string>
  is Stream<Type> {
  @header contentType: typeof ContentType;
  @body body: BodyType;
}

/**
 * Describes a stream of JSON data with one JSON object per line and sets
 * the content type to `application/jsonl`.
 *
 * The JSON data is described by `Type`.
 *
 * @template Type The set of models describing the JSON data in the stream.
 *
 * @example
 *
 * ```typespec
 * model Message {
 *   id: string;
 *   text: string;
 * }
 *
 * @TypeSpec.Events.events
 * union Events {
 *   Message,
 * }
 *
 * op subscribe(): JsonlStream<Events>;
 * ```
 */
@doc("")
model JsonlStream<Type> is HttpStream<Type, "application/jsonl">;
