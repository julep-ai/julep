import "../common";
import "../sessions";
import "./models.tsp";

using Common;
using Sessions;

namespace Entries;

//
// ENTRY ENDPOINTS
//

interface Endpoints
    extends ChildLimitOffsetPagination<
            History,
            "Get history of a Session (paginated)"
        >,
        DeleteEndpoint<"Clear the history of a Session (resets the Session)"> {}
