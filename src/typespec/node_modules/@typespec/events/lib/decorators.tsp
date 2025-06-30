using TypeSpec.Reflection;

namespace TypeSpec.Events;

/**
 * Specify that this union describes a set of events.
 *
 * @example
 *
 * ```typespec
 * @events
 * union MixedEvents {
 *   pingEvent: string;
 *
 *   doneEvent: "done";
 * }
 * ```
 */
extern dec events(target: Union);

/**
 * Specifies the content type of the event envelope, event body, or event payload.
 * When applied to an event payload, that field must also have a corresponding `@data`
 * decorator.
 *
 * @example
 *
 * ```typespec
 * @events union MixedEvents {
 *   @contentType("application/json")
 *   message: { id: string, text: string, }
 * }
 * ```
 *
 * @example Specify the content type of the event payload.
 *
 * ```typespec
 * @events union MixedEvents {
 *   { done: true },
 *
 *   { done: false, @data @contentType("text/plain") value: string,}
 * }
 * ```
 */
extern dec contentType(target: UnionVariant | ModelProperty, contentType: valueof string);

/**
 * Identifies the payload of an event.
 * Only one field in an event can be marked as the payload.
 *
 * @example
 *
 * ```typespec
 * @events union MixedEvents {
 *   { metadata: Record<string>, @data payload: string,}
 * }
 * ```
 */
extern dec data(target: ModelProperty);
