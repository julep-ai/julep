import "@typespec/http";
import "../dist/src/internal-decorators.js";

namespace TypeSpec.Rest.Resource;

using TypeSpec.Http;

@doc("The default error response for resource operations.")
model ResourceError {
  @doc("The error code.")
  code: int32;

  @doc("The error message.")
  message: string;
}

/**
 * Dynamically gathers keys of the model type `Resource`.
 *
 * @template Resource The target resource model.
 */
@doc("Dynamically gathers keys of the model type Resource.")
@copyResourceKeyParameters
@friendlyName("{name}Key", Resource)
model KeysOf<Resource> {}

/**
 * Dynamically gathers parent keys of the model type `Resource`.
 *
 * @template Resource The target resource model.
 */
@doc("Dynamically gathers parent keys of the model type Resource.")
@copyResourceKeyParameters("parent")
@friendlyName("{name}ParentKey", Resource)
model ParentKeysOf<Resource> {}

/**
 * Represents operation parameters for the resource of type `Resource`.
 *
 * @template Resource The resource model.
 */
@doc("Represents operation parameters for resource Resource.")
model ResourceParameters<Resource extends {}> {
  ...KeysOf<Resource>;
}

/**
 * Represents collection operation parameters for the resource of type `Resource`.
 *
 * @template Resource The resource model.
 */
@doc("Represents collection operation parameters for resource Resource.")
model ResourceCollectionParameters<Resource extends {}> {
  ...ParentKeysOf<Resource>;
}

/**
 * Represents the resource GET operation.
 *
 * @template Resource The resource model.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface ResourceRead<Resource extends {}, Error> {
  /**
   * Gets an instance of the resource.
   *
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Gets an instance of the resource.")
  @readsResource(Resource)
  get(...ResourceParameters<Resource>): Resource | Error;
}

/**
 * Resource create operation completed successfully.
 *
 * @template Resource The resource model that was created.
 */
@doc("Resource create operation completed successfully.")
model ResourceCreatedResponse<Resource> {
  ...CreatedResponse;
  @bodyRoot body: Resource;
}

/**
 * Resource create or replace operation template.
 *
 * @template Resource The resource model to create or replace.
 * @template Error The error response.
 */
interface ResourceCreateOrReplace<Resource extends {}, Error> {
  /**
   * Creates or replaces a instance of the resource.
   *
   * @template Resource The resource model to create or replace.
   * @template Error The error response.
   */
  @autoRoute
  @doc("Creates or replaces an instance of the resource.")
  @createsOrReplacesResource(Resource)
  createOrReplace(
    ...ResourceParameters<Resource>,
    @bodyRoot resource: ResourceCreateModel<Resource>,
  ): Resource | ResourceCreatedResponse<Resource> | Error;
}

/**
 * Resource create or update operation model.
 *
 * @template Resource The resource model to create or update.
 */
@friendlyName("{name}Update", Resource)
model ResourceCreateOrUpdateModel<Resource extends {}>
  is OptionalProperties<UpdateableProperties<DefaultKeyVisibility<Resource, "read">>>;

/**
 * Resource create or update operation template.
 *
 * @template Resource The resource model to create or update.
 * @template Error The error response.
 */
interface ResourceCreateOrUpdate<Resource extends {}, Error> {
  /**
   * Creates or update an instance of the resource.
   *
   * @template Resource The resource model to create or update.
   * @template Error The error response.
   */
  @autoRoute
  @doc("Creates or update an instance of the resource.")
  @createsOrUpdatesResource(Resource)
  createOrUpdate(
    ...ResourceParameters<Resource>,
    @bodyRoot resource: ResourceCreateOrUpdateModel<Resource>,
  ): Resource | ResourceCreatedResponse<Resource> | Error;
}

/**
 * Resource create operation model.
 *
 * @template Resource The resource model to create.
 */
@friendlyName("{name}Create", Resource)
@withVisibility("create")
model ResourceCreateModel<Resource extends {}> is DefaultKeyVisibility<Resource, "read">;

/**
 * Resource create operation template.
 *
 * @template Resource The resource model to create.
 * @template Error The error response.
 */
interface ResourceCreate<Resource extends {}, Error> {
  /**
   * Creates a new instance of the resource.
   *
   * @template Resource The resource model to create.
   * @template Error The error response.
   */
  @autoRoute
  @doc("Creates a new instance of the resource.")
  @createsResource(Resource)
  create(
    ...ResourceCollectionParameters<Resource>,
    @bodyRoot resource: ResourceCreateModel<Resource>,
  ): Resource | ResourceCreatedResponse<Resource> | Error;
}

/**
 * Resource update operation template.
 *
 * @template Resource The resource model to update.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface ResourceUpdate<Resource extends {}, Error> {
  /**
   * Updates an existing instance of the resource.
   *
   * @template Resource The resource model to update.
   * @template Error The error response.
   */
  @autoRoute
  @doc("Updates an existing instance of the resource.")
  @updatesResource(Resource)
  update(
    ...ResourceParameters<Resource>,
    @bodyRoot properties: ResourceCreateOrUpdateModel<Resource>,
  ): Resource | Error;
}

@doc("Resource deleted successfully.")
model ResourceDeletedResponse {
  @doc("The status code.")
  @statusCode
  _: 200;
}

/**
 * Resource delete operation template.
 *
 * @template Resource The resource model to delete.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface ResourceDelete<Resource extends {}, Error> {
  /**
   * Deletes an existing instance of the resource.
   *
   * @template Resource The resource model to delete.
   * @template Error The error response.
   */
  @autoRoute
  @doc("Deletes an existing instance of the resource.")
  @deletesResource(Resource)
  delete(...ResourceParameters<Resource>): ResourceDeletedResponse | Error;
}

/**
 * Structure for a paging response using `value` and `nextLink` to represent pagination.
 *
 * This only provides the model structure and not actual pagination support. See
 * https://github.com/microsoft/typespec/issues/705 for general paging support.
 *
 * @template Resource The resource type of the collection.
 */
@doc("Paged response of {name} items", Resource)
@friendlyName("{name}CollectionWithNextLink", Resource)
model CollectionWithNextLink<Resource extends {}> {
  @doc("The items on this page")
  value: Resource[];

  @doc("The link to the next page of items")
  nextLink?: ResourceLocation<Resource>;
}

/**
 * Resource list operation template.
 *
 * @template Resource The resource model to list.
 * @template Error The error response.
 */
interface ResourceList<Resource extends {}, Error> {
  /**
   * Lists all instances of the resource.
   *
   * @template Resource The resource model to list.
   * @template Error The error response.
   */
  @autoRoute
  @doc("Lists all instances of the resource.")
  @listsResource(Resource)
  list(...ResourceCollectionParameters<Resource>): CollectionWithNextLink<Resource> | Error;
}

/**
 * Resource operation templates for resource instances.
 *
 * @template Resource The resource model.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface ResourceInstanceOperations<Resource extends {}, Error>
  extends ResourceRead<Resource, Error>,
    ResourceUpdate<Resource, Error>,
    ResourceDelete<Resource, Error> {}

/**
 * Resource operation templates for resource collections.
 *
 * @template Resource The resource model.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface ResourceCollectionOperations<Resource extends {}, Error>
  extends ResourceCreate<Resource, Error>,
    ResourceList<Resource, Error> {}

/**
 * Resource operation templates for resources.
 *
 * @template Resource The resource model.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface ResourceOperations<Resource extends {}, Error>
  extends ResourceInstanceOperations<Resource, Error>,
    ResourceCollectionOperations<Resource, Error> {}

/**
 * Singleton resource read operation template.
 *
 * @template Singleton The singleton resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface SingletonResourceRead<Singleton extends {}, Resource extends {}, Error> {
  /**
   * Gets the singleton resource.
   *
   * @template Singleton The singleton resource model.
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Gets the singleton resource.")
  @segmentOf(Singleton)
  @readsResource(Singleton)
  get(...ResourceParameters<Resource>): Singleton | Error;
}

/**
 * Singleton resource update operation template.
 *
 * @template Singleton The singleton resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface SingletonResourceUpdate<Singleton extends {}, Resource extends {}, Error> {
  /**
   * Updates the singleton resource.
   *
   * @template Singleton The singleton resource model.
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Updates the singleton resource.")
  @segmentOf(Singleton)
  @updatesResource(Singleton)
  update(
    ...ResourceParameters<Resource>,

    @body
    properties: ResourceCreateOrUpdateModel<Singleton>,
  ): Singleton | Error;
}

/**
 * Singleton resource operation templates for singleton resource instances.
 *
 * @template Singleton The singleton resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface SingletonResourceOperations<Singleton extends {}, Resource extends {}, Error>
  extends SingletonResourceRead<Singleton, Resource, Error>,
    SingletonResourceUpdate<Singleton, Resource, Error> {}

/**
 * Extension resource read operation template.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
@Private.validateHasKey(Resource)
@Private.validateIsError(Error)
interface ExtensionResourceRead<Extension extends {}, Resource extends {}, Error> {
  /**
   * Gets an instance of the extension resource.
   *
   * @template Extension The extension resource model.
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Gets an instance of the extension resource.")
  @readsResource(Extension)
  get(...ResourceParameters<Resource>, ...ResourceParameters<Extension>): Extension | Error;
}

/**
 * Extension resource create or update operation template.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface ExtensionResourceCreateOrUpdate<Extension extends {}, Resource extends {}, Error> {
  /**
   * Creates or update an instance of the extension resource.
   *
   * @template Extension The extension resource model.
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Creates or update an instance of the extension resource.")
  @createsOrUpdatesResource(Extension)
  createOrUpdate(
    ...ResourceParameters<Resource>,
    ...ResourceParameters<Extension>,
    @bodyRoot resource: ResourceCreateOrUpdateModel<Extension>,
  ): Extension | ResourceCreatedResponse<Extension> | Error;
}

/**
 * Extension resource create operation template.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface ExtensionResourceCreate<Extension extends {}, Resource extends {}, Error> {
  /**
   * Creates a new instance of the extension resource.
   *
   * @template Extension The extension resource model.
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Creates a new instance of the extension resource.")
  @createsResource(Extension)
  create(
    ...ResourceParameters<Resource>,
    @bodyRoot resource: ResourceCreateModel<Extension>,
  ): Extension | ResourceCreatedResponse<Extension> | Error;
}

/**
 * Extension resource update operation template.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface ExtensionResourceUpdate<Extension extends {}, Resource extends {}, Error> {
  /**
   * Updates an existing instance of the extension resource.
   *
   * @template Extension The extension resource model.
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Updates an existing instance of the extension resource.")
  @updatesResource(Extension)
  update(
    ...ResourceParameters<Resource>,
    ...ResourceParameters<Extension>,

    @body
    properties: ResourceCreateOrUpdateModel<Extension>,
  ): Extension | Error;
}

/**
 * Extension resource delete operation template.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface ExtensionResourceDelete<Extension extends {}, Resource extends {}, Error> {
  /**
   * Deletes an existing instance of the extension resource.
   *
   * @template Extension The extension resource model.
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Deletes an existing instance of the extension resource.")
  @deletesResource(Extension)
  delete(
    ...ResourceParameters<Resource>,
    ...ResourceParameters<Extension>,
  ): ResourceDeletedResponse | Error;
}

/**
 * Extension resource list operation template.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface ExtensionResourceList<Extension extends {}, Resource extends {}, Error> {
  /**
   * Lists all instances of the extension resource.
   *
   * @template Extension The extension resource model.
   * @template Resource The resource model.
   */
  @autoRoute
  @doc("Lists all instances of the extension resource.")
  @listsResource(Extension)
  list(
    ...ResourceParameters<Resource>,
    ...ResourceCollectionParameters<Extension>,
  ): CollectionWithNextLink<Extension> | Error;
}

/**
 * Extension resource operation templates for extension resource instances.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface ExtensionResourceInstanceOperations<Extension extends {}, Resource extends {}, Error>
  extends ExtensionResourceRead<Extension, Resource, Error>,
    ExtensionResourceUpdate<Extension, Resource, Error>,
    ExtensionResourceDelete<Extension, Resource, Error> {}

/**
 * Extension resource operation templates for extension resource collections.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface ExtensionResourceCollectionOperations<Extension extends {}, Resource extends {}, Error>
  extends ExtensionResourceCreate<Extension, Resource, Error>,
    ExtensionResourceList<Extension, Resource, Error> {}

/**
 * Extension resource operation templates for extension resource instances and collections.
 *
 * @template Extension The extension resource model.
 * @template Resource The resource model.
 * @template Error The error response.
 */
interface ExtensionResourceOperations<Extension extends {}, Resource extends {}, Error>
  extends ExtensionResourceInstanceOperations<Extension, Resource, Error>,
    ExtensionResourceCollectionOperations<Extension, Resource, Error> {}
