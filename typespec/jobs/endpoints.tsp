import "../common";
import "./models.tsp";

using Common;

namespace Jobs;

//
// JOB ENDPOINTS
//

interface Endpoints
    extends GetEndpoint<
            JobStatus,
            "Get the status of an existing Job by its id"
        > {}
