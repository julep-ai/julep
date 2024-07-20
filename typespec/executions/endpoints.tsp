import "../common";
import "./models.tsp";

using Common;

namespace Executions;

//
// EXECUTION ENDPOINTS
//

interface Endpoints
    extends UpdateEndpoint<
            UpdateExecutionRequest,
            "Update an existing Execution"
        >,
        GetEndpoint<Execution, "Get an Execution by id"> {}

interface TransitionEndpoints
    extends ChildLimitOffsetPagination<
            {
                transitions: Transition[],
            },
            "List the Transitions of an Execution by id"
        > {}
