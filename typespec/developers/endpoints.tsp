import "./models.tsp";
import "../common";

using TypeSpec.Http;
using TypeSpec.OpenAPI;
using TypeSpec.Versioning;
using Common;
using Developers;

namespace Developers;

/** API endpoints for developers */
interface Endpoints {
    @summary("Create a Developer")
    @doc("Create a new developer account")
    @post
    createDeveloper(@body developer: CreateDeveloperRequest): Developer;

    @summary("Get a Developer")
    @doc("Get a developer's details")
    @get
    getDeveloper(@path id: uuid): Developer;

    @summary("Update a Developer")
    @doc("Update a developer's details")
    @put
    updateDeveloper(@path id: uuid, @body developer: UpdateDeveloperRequest): Developer;

    @summary("Patch a Developer")
    @doc("Patch a developer's details")
    @patch
    patchDeveloper(@path id: uuid, @body developer: PatchDeveloperRequest): Developer;
}