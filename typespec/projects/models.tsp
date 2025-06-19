import "@typespec/http";

import "../common";

using TypeSpec.Http;

using Common;

namespace Projects;

//
// PROJECT MODELS
//

@doc("Project model")
model Project {
  ...HasId;
  ...HasMetadata;
  ...HasTimestamps;

  @doc("Canonical name of the project (unique per developer)")
  canonical_name?: canonicalName;

  @doc("Display name of the project")
  name: displayName;

}

/** Payload for updating a project */
@withVisibility(Lifecycle.Create, Lifecycle.Update)
model UpdateProjectRequest {
    ...Project;
}

/** Payload for patching a project */
model PatchProjectRequest is UpdateProjectRequest {}

/** Payload for creating a project */
@withVisibility(Lifecycle.Create)
model CreateProjectRequest {
    ...UpdateProjectRequest;
}

model CreateOrUpdateProjectRequest extends CreateProjectRequest {
    @path
    id: uuid;
    ...UpdateProjectRequest;
}
