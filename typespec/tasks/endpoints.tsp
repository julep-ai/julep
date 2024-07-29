import "../common";
import "../executions";
import "./models.tsp";

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