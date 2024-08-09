import "@typespec/http";

import "../common";
import "./models.tsp";

using TypeSpec.Http;

using Common;

namespace Executions;

//
// EXECUTION ENDPOINTS
//

interface Endpoints
    extends GetEndpoint<Execution, "Get an Execution by id">,
        UpdateEndpoint<UpdateExecutionRequest, "Update an existing Execution"> {}
    
interface PublicEndpoints {
    @post
    @useAuth([])
    @doc("Resume an execution with a task token")
    op resumeWithTaskToken(
        @header contentType: json,

        // Uses a query parameter `task_token` to get the task token
        // See `TaskTokenResumeExecutionRequest` for more details

        @bodyRoot
        @doc("Request to resume an execution with a task token")
        body: TaskTokenResumeExecutionRequest,
    ): {
        @statusCode _: "200";

        @body
        @doc("Response of resuming the execution with the ID found")
        body: ResourceUpdatedResponse;
    };
}

interface TaskEndpoints
    extends ChildCreateEndpoint<
            CreateExecutionRequest,
            "Create an execution for the given task"
        >,
        ChildLimitOffsetPagination<
            Execution,
            "List executions of the given task"
        > {}

interface TransitionEndpoints
    extends ChildLimitOffsetPagination<
            {
                transitions: Transition[],
            },
            "List the Transitions of an Execution by id"
        > {}
