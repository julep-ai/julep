export function createTracer(logger, tracerOptions = {}) {
    const filters = tracerOptions.filter ? createFilterTree(tracerOptions.filter) : undefined;
    function shouldTrace(area) {
        if (!filters) {
            return false;
        }
        return filters.match(area);
    }
    function log(area, message) {
        if (shouldTrace(area)) {
            logger.log({
                level: "trace",
                code: area,
                message,
            });
        }
    }
    return createTracerInternal(log);
}
function createFilterTree(filters) {
    const tree = {
        all: false,
        children: {},
    };
    for (const filter of filters) {
        if (tree.all) {
            break;
        }
        let current = tree;
        const segments = filter.split(".");
        for (const segment of segments) {
            if (current.all) {
                break;
            }
            if (segment === "*") {
                current.all = true;
                break;
            }
            current.children[segment] = {
                all: false,
                children: {},
            };
            current = current.children[segment];
        }
        current.all = true;
    }
    return { match };
    function match(area) {
        if (tree.all) {
            return true;
        }
        const segments = area.split(".");
        let current = tree;
        for (const segment of segments) {
            if (current.all) {
                return true;
            }
            if (!current.children[segment]) {
                return false;
            }
            current = current.children[segment];
        }
        return true;
    }
}
function createTracerInternal(log) {
    return {
        trace,
        sub,
    };
    function trace(area, message) {
        log(area, message);
    }
    function sub(subArea) {
        return createTracerInternal((area, message) => {
            log(joinAreas(subArea, area), message);
        });
    }
}
function joinAreas(a, b) {
    if (a) {
        if (b) {
            return `${a}.${b}`;
        }
        return a;
    }
    else {
        return b ?? "";
    }
}
//# sourceMappingURL=tracer.js.map