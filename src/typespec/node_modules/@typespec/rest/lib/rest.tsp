import "@typespec/http";
import "./rest-decorators.tsp";
import "./resource.tsp";
import "../dist/src/tsp-index.js";

namespace TypeSpec.Rest;

/**
 * A URL that points to a resource.
 * @template Resource The type of resource that the URL points to.
 */
@doc("The location of an instance of {name}", Resource)
@Private.resourceLocation(Resource)
scalar ResourceLocation<Resource extends {}> extends url;
