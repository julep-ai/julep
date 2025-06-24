import "../common";
import "./models.tsp";

using Common;

namespace Files;

//
// FILE ENDPOINTS
//

interface Endpoints
    extends GetEndpoint<File, "Get a File by its id">,
        CreateEndpoint<CreateFileRequest, File, "Create a new File"> {}

interface UserEndpoints
    extends ChildLimitOffsetPagination<File, "List Files owned by a User">,
        ChildDeleteEndpoint<"Delete a File for this User">,
        ChildCreateEndpoint<CreateFileRequest, File, "Create a File for this User"> {}

interface AgentEndpoints
    extends ChildLimitOffsetPagination<File, "List Files owned by an Agent">,
        ChildDeleteEndpoint<"Delete a File for this Agent">,
        ChildCreateEndpoint<CreateFileRequest, File, "Create a File for this Agent"> {}
