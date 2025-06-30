namespace TypeSpec;

/**
 * Represent a 32-bit unix timestamp datetime with 1s of granularity.
 * It measures time by the number of seconds that have elapsed since 00:00:00 UTC on 1 January 1970.
 */
@encode("unixTimestamp", int32)
scalar unixTimestamp32 extends utcDateTime;

/**
 * Represent a model
 */
// Deprecated June 2023 sprint
#deprecated "object is deprecated. Please use {} for an empty model, `Record<unknown>` for a record with unknown property types, `unknown[]` for an array."
model object {}

/**
 * Represent a URL string as described by https://url.spec.whatwg.org/
 */
scalar url extends string;

/**
 * Represents a collection of optional properties.
 *
 * @template Source An object whose spread properties are all optional.
 */
@doc("The template for adding optional properties.")
@withOptionalProperties
model OptionalProperties<Source> {
  ...Source;
}

/**
 * Represents a collection of updateable properties.
 *
 * @template Source An object whose spread properties are all updateable.
 */
@doc("The template for adding updateable properties.")
@withUpdateableProperties
model UpdateableProperties<Source> {
  ...Source;
}

/**
 * Represents a collection of omitted properties.
 *
 * @template Source An object whose properties are spread.
 * @template Keys The property keys to omit.
 */
@doc("The template for omitting properties.")
@withoutOmittedProperties(Keys)
model OmitProperties<Source, Keys extends string> {
  ...Source;
}

/**
 * Represents a collection of properties with only the specified keys included.
 *
 * @template Source An object whose properties are spread.
 * @template Keys The property keys to include.
 */
@doc("The template for picking properties.")
@withPickedProperties(Keys)
model PickProperties<Source, Keys extends string> {
  ...Source;
}

/**
 * Represents a collection of properties with default values omitted.
 *
 * @template Source An object whose spread property defaults are all omitted.
 */
@withoutDefaultValues
model OmitDefaults<Source> {
  ...Source;
}

/**
 * Applies a visibility setting to a collection of properties.
 *
 * @template Source An object whose properties are spread.
 * @template Visibility The visibility to apply to all properties.
 */
@doc("The template for setting the default visibility of key properties.")
@withDefaultKeyVisibility(Visibility)
model DefaultKeyVisibility<Source, Visibility extends valueof string> {
  ...Source;
}
