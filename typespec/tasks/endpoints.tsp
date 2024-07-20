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

interface Endpoints
    extends UpdateEndpoint<
            UpdateTaskRequest,
            "Update an existing task (overwrite existing values)"
        >,
        PatchEndpoint<
            PatchTaskRequest,
            "Update an existing task (merges with existing values)"
        >,
        DeleteEndpoint<"Delete a task by its id">,
        LimitOffsetPagination<Task, "List tasks (paginated)">,
        CreateOrUpdateEndpoint<
            CreateOrUpdateTaskRequest,
            "Create or update a task"
        >,
        CreateEndpoint<CreateTaskRequest, "Create a new task"> {}

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
