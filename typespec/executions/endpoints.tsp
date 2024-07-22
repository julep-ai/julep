import "../common";
import "./models.tsp";

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
        > {}

interface TransitionEndpoints
    extends ChildLimitOffsetPagination<
            {
                transitions: Transition[],
            },
            "List the Transitions of an Execution by id"
        > {}
