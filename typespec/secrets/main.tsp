import "@typespec/rest";
import "@typespec/openapi";
import "@typespec/versioning";
import "@typespec/http";
import "./models.tsp";
import "./endpoints.tsp";
import "../versions.tsp";

using TypeSpec.Http;
using TypeSpec.Rest;
using TypeSpec.Versioning;
using Versions;

@versioned(ApiVersions)
namespace Julep.Secrets; 