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

interface GetEndpoints extends GetEndpoint<Task, "Get a task by id"> {}

interface CreateOrUpdateEndpoints {
    @post
    @doc("Create or update a task")
    createOrUpdate(
        @header contentType: yaml | json,

        @path
        @doc("ID of the agent")
        parent_id: uuid,

        ...CreateOrUpdateTaskRequest,
    ): {
        @statusCode _: "201";

        @body
        @doc("Details of the task updated along with ID")
        body: ResourceUpdatedResponse;
    };
}

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
        ChildLimitOffsetPagination<Task, "List tasks (paginated)"> {
    @post
    @doc("Create a new task")
    create(
        @header contentType: yaml | json,

        @path
        @doc("ID of parent resource")
        id: uuid,

        ...CreateTaskRequest,
    ): {
        @statusCode _: "200";

        @body
        @doc("Details of the task created")
        body: ResourceCreatedResponse;
    };
}
