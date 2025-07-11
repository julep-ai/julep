namespace Common;

//
// COMMON SCALARS
//

@format("uuid")
scalar uuid extends string;

alias concreteType = numeric | string | boolean | null;

/**
 * For Unicode character safety
 * See: https://unicode.org/reports/tr31/
 * See: https://www.unicode.org/reports/tr39/#Identifier_Characters
 */
@maxLength(120)
@pattern("^[\\p{L}\\p{Nl}\\p{Pattern_Syntax}\\p{Pattern_White_Space}]+[\\p{ID_Start}\\p{Mn}\\p{Mc}\\p{Nd}\\p{Pc}\\p{Pattern_Syntax}\\p{Pattern_White_Space}]*$")
scalar identifierSafeUnicode extends string;

/** Valid mime types */
@maxLength(120)
@pattern("^(application|audio|font|example|image|message|model|multipart|text|video|x-(?:[0-9A-Za-z!#$%&'*+.^_`|~-]+))\\/([0-9A-Za-z!#$%&'*+.^_`|~-]+)$")
scalar mimeType extends string;

/** Valid python identifier names */
@pattern("^[^\\W0-9]\\w*$")
@maxLength(40)
scalar validPythonIdentifier extends string;

/** A valid step label */
@maxLength(120)
@pattern("^[^0-9]|^[0-9]+[^0-9].*$")
scalar stepLabel extends string;

/** Limit the number of results */
@minValue(1)
@maxValueExclusive(1000)
scalar limit extends uint16;

/** Offset to apply to the results */
@minValue(0)
scalar offset extends uint32;

/** Sort by a field */
alias sortBy = "created_at" | "updated_at";

/** Sort direction */
alias sortDirection = "asc" | "desc";

/** Contents of a document */
@maxLength(30000)
scalar content extends string;

@minValue(-100.0)
@maxValue(100.0)
scalar logit_bias extends float32;

/** YAML Mime Type; see: https://stackoverflow.com/questions/332129/yaml-media-type */
alias yaml = "application/yaml" | "text/x-yaml" | "text/yaml";
alias json = "application/json";
alias eventStream = "text/event-stream";

/** Different possible sources that can produce new entries */
alias entrySource =
    | "api_request"
    | "api_response"
    | "tool_request"
    | "tool_response"
    | "internal"
    | "summarizer"
    | "meta";

/** A simple python expression compatible with SimpleEval. */
scalar PyExpression extends string;

/** A valid jinja template. */
scalar JinjaTemplate extends string;

/**
 * For canonical names (machine-friendly identifiers)
 * Must start with a letter and can only contain letters, numbers, and underscores
 */
@minLength(1)
@maxLength(255)
@pattern("^[a-zA-Z][a-zA-Z0-9_]*$")
scalar canonicalName extends string;

/**
 * For display names
 * Must be between 1 and 255 characters
 */
@minLength(1)
@maxLength(255)
scalar displayName extends string;
