import "@typespec/http/streams";

using Http.Streams;

namespace TypeSpec.SSE;

/**
 * Describes a stream of server-sent events.
 *
 * The content-type is set to `text/event-stream`.
 *
 * The server-sent events are described by `Type`.
 * The event type for any event can be defined by using named union variants.
 * When a union variant is not named, it is considered a 'message' event.
 *
 * @template Type The set of models describing the server-sent events.
 *
 * @example Mix of named union variants and terminal event
 *
 * ```typespec
 * model UserConnect {
 *   username: string;
 *   time: string;
 * }
 *
 * model UserMessage {
 *   username: string;
 *   time: string;
 *   text: string;
 * }
 *
 * model UserDisconnect {
 *   username: string;
 *   time: string;
 * }
 *
 * @TypeSpec.Events.events
 * union ChannelEvents {
 *   userconnect: UserConnect,
 *   usermessage: UserMessage,
 *   userdisconnect: UserDisconnect,
 *
 *   @Events.contentType("text/plain")
 *   @terminalEvent
 *   "[unsubscribe]",
 * }
 *
 * op subscribeToChannel(): SSEStream<ChannelEvents>;
 * ```
 */
@doc("")
model SSEStream<Type extends TypeSpec.Reflection.Union> is HttpStream<Type, "text/event-stream">;
