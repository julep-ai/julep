import "@typespec/http";
import "@typespec/openapi";

import "../common";
import "./models.tsp";

using Common;

namespace Jobs;

//
// JOB ENDPOINTS
//

interface Endpoints extends GetEndpoint<JobStatus, "JobStatus"> {}