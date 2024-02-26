// base.js
/**
 * Purpose: Base class for all managers
 */
class BaseManager {
    /**
     * A class that serves as a base manager for working with different API clients.
     * @param {JulepApi} api_client An instance of JulepApi to be used by this class.
     */
    constructor(api_client) {
        this.api_client = api_client;
    }
}

exports.BaseManager = BaseManager;
