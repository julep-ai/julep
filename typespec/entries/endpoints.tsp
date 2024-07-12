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
            "History",
            Session,
            "Session"
        >,
        DeleteEndpoint<History, "History"> {}
