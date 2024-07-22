import "@typespec/http";

import "../common";
import "../executions";
import "./models.tsp";

using TypeSpec.Http;

using Common;
using Executions;

namespace Tasks;

//
// TASK ENDPOINTS
//

interface CreateOrUpdateEndpoints
    extends ChildCreateOrUpdateEndpoint<
            CreateOrUpdateTaskRequest,
            "Create or update a task"
        > {}

interface Endpoints
    extends ChildUpdateEndpoint<
            UpdateTaskRequest,
            "Update an existing task (overwrite existing values)"
        >,
        ChildPatchEndpoint<
            PatchTaskRequest,
            "Update an existing task (merges with existing values)"
        >,
        ChildDeleteEndpoint<"Delete a task by its id">,
        ChildLimitOffsetPagination<Task, "List tasks (paginated)">,
        ChildCreateEndpoint<CreateTaskRequest, "Create a new task"> {}

interface ExecutionEndpoints
    extends ChildCreateEndpoint<
            CreateExecutionRequest,
            "Create an execution for the given task"
        >,
        ChildLimitOffsetPagination<Execution, "List executions of the given task"> {
    @put
    @doc("Resume an execution with a task token")
    resumeWithTaskToken(
        @header contentType: yaml | json,

        @path
        @doc("ID of parent Task")
        id: uuid,

        @body
        @doc("Request to resume an execution with a task token")
        body: TaskTokenResumeExecutionRequest,
    ): {
        @statusCode _: "200";

        @body
        @doc("Response of resuming the execution with the ID found")
        body: ResourceUpdatedResponse;
    };
}
