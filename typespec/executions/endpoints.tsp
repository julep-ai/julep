import "../common";
import "./models.tsp";

using Common;

namespace Executions;

//
// EXECUTION ENDPOINTS
//

interface Endpoints
    extends UpdateEndpoint<Execution, "Execution", UpdateExecutionRequest>,
        GetEndpoint<Execution, "Execution"> {}

interface TransitionEndpoints
    extends ChildLimitOffsetPagination<
            {
                transitions: Transition[],
            },
            "Transitions",
            Execution,
            "Execution"
        > {}
