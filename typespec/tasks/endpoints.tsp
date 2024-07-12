import "../common";
import "./models.tsp";

using Common;

namespace Tasks;

//
// Task ENDPOINTS
//

interface Endpoints
    extends UpdateEndpoint<Task, "Task", UpdateTaskRequest>,
        PatchEndpoint<Task, "Task", PatchTaskRequest>,
        DeleteEndpoint<Task, "Task">,
        LimitOffsetPagination<Task, "Task">,
        CreateOrUpdateEndpoint<Task, "Task", CreateOrUpdateTaskRequest>,
        CreateEndpoint<Task, "Task", CreateTaskRequest> {}
