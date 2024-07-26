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
    extends GetEndpoint<Execution, "Get an Execution by id"> {}

interface TaskEndpoints
    extends ChildUpdateEndpoint<
            UpdateExecutionRequest,
            "Update an existing Execution"
        >,
        ChildCreateEndpoint<
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

interface TransitionEndpoints
    extends ChildLimitOffsetPagination<
            {
                transitions: Transition[],
            },
            "List the Transitions of an Execution by id"
        > {}
