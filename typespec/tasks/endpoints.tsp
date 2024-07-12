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
    extends UpdateEndpoint<Task, "Task", UpdateTaskRequest>,
        PatchEndpoint<Task, "Task", PatchTaskRequest>,
        DeleteEndpoint<Task, "Task">,
        LimitOffsetPagination<Task, "Task">,
        CreateOrUpdateEndpoint<Task, "Task", CreateOrUpdateTaskRequest>,
        CreateEndpoint<Task, "Task", CreateTaskRequest> {}

interface ExecutionEndpoints
    extends ChildCreateEndpoint<Execution, "Execution", Task, "Task", CreateExecutionRequest>,
        ChildLimitOffsetPagination<Execution, "Execution", Task, "Task"> {
            @put
            @doc("Resume an execution with a task token")
            resumeWithTaskToken(
                @header contentType: yaml | json;

                @path
                @doc("ID of parent Task")
                id: uuid,

                @body
                @doc("Request to resume an execution with a task token")
                body: TaskTokenResumeExecutionRequest;
            ): {
                @statusCode _: "200";

                @body
                @doc("Response of resuming the execution with the ID found")
                body: ResourceUpdatedResponse<Execution, "Execution">;
            };
        }