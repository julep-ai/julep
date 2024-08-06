import "@typespec/http";

import "../common";
import "../sessions";
import "./models.tsp";

using TypeSpec.Http;

using Common;
using Sessions;

namespace Entries;

//
// ENTRY ENDPOINTS
//

interface Endpoints
    extends DeleteEndpoint<"Clear the history of a Session (resets the Session)"> {
    @get
    @doc("Get history of a Session")
    history(
        @path
        @doc("ID of parent")
        id: uuid,
    ): History;
}
