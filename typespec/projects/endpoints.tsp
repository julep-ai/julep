import "@typespec/http";
import "../common";
import "./models.tsp";

using TypeSpec.Http;
using Common;

namespace Projects;

//
// PROJECT ENDPOINTS
//

interface Endpoints
    extends LimitOffsetPagination<Project, "List Projects (paginated)">,
        CreateEndpoint<CreateProjectRequest, Project, "Create a new Project">,
        CreateOrUpdateEndpoint<CreateOrUpdateProjectRequest, Project, "Create or update a Project">,
        UpdateEndpoint<UpdateProjectRequest, Project, "Update an existing Project by id (overwrites existing values; use PATCH for merging instead)">,
        PatchEndpoint<PatchProjectRequest, Project, "Update an existing Project by id (merges with existing values)">,
        DeleteEndpoint<"Delete Project by id">,
        GetEndpoint<Project, "Get a Project by id"> {
}
