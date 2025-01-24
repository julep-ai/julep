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
