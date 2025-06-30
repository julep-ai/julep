using TypeSpec.Reflection;

namespace TypeSpec.OpenAPI;

/**
 * Specify the OpenAPI `operationId` property for this operation.
 *
 * @param operationId Operation id value.
 *
 * @example
 *
 * ```typespec
 * @operationId("download")
 * op read(): string;
 * ```
 */
extern dec operationId(target: Operation, operationId: valueof string);

/**
 * Attach some custom data to the OpenAPI element generated from this type.
 *
 * @param key Extension key. Must start with `x-`
 * @param value Extension value.
 *
 * @example
 *
 * ```typespec
 * @extension("x-custom", "My value")
 * @extension("x-pageable", {nextLink: "x-next-link"})
 * op read(): string;
 * ```
 */
extern dec extension(target: unknown, key: valueof string, value: unknown);

/**
 * Specify that this model is to be treated as the OpenAPI `default` response.
 * This differs from the compiler built-in `@error` decorator as this does not necessarily represent an error.
 *
 * @example
 *
 * ```typespec
 * @defaultResponse
 * model PetStoreResponse is object;
 *
 * op listPets(): Pet[] | PetStoreResponse;
 * ```
 */
extern dec defaultResponse(target: Model);

/**
 * Specify the OpenAPI `externalDocs` property for this type.
 *
 * @param url Url to the docs
 * @param description Description of the docs
 *
 * @example
 * ```typespec
 * @externalDocs("https://example.com/detailed.md", "Detailed information on how to use this operation")
 * op listPets(): Pet[];
 * ```
 */
extern dec externalDocs(target: unknown, url: valueof string, description?: valueof string);

/** Additional information for the OpenAPI document. */
model AdditionalInfo {
  /** The title of the API. Overrides the `@service` title. */
  title?: string;

  /** A short summary of the API. Overrides the `@summary` provided on the service namespace. */
  summary?: string;

  /** The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API implementation version). */
  version?: string;

  /** A URL to the Terms of Service for the API. MUST be in the format of a URL. */
  termsOfService?: url;

  /** The contact information for the exposed API. */
  contact?: Contact;

  /** The license information for the exposed API. */
  license?: License;
}

/** Contact information for the exposed API. */
model Contact {
  /** The identifying name of the contact person/organization. */
  name?: string;

  /** The URL pointing to the contact information. MUST be in the format of a URL. */
  url?: url;

  /** The email address of the contact person/organization. MUST be in the format of an email address. */
  email?: string;
}

/** License information for the exposed API. */
model License {
  /** The license name used for the API. */
  name: string;

  /** A URL to the license used for the API. MUST be in the format of a URL. */
  url?: url;
}

/**
 * Specify OpenAPI additional information.
 * The service `title` and `version` are already specified using `@service`.
 * @param additionalInfo Additional information
 */
extern dec info(target: Namespace, additionalInfo: AdditionalInfo);
