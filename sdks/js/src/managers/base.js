// base.js
/**
 * Purpose: Base class for all managers
 */
class BaseManager {
    /**
     * A class that serves as a base manager for working with different API clients.
     * @param {JulepApi} apiClient An instance of JulepApi to be used by this class.
     */
    constructor(apiClient) {
        this.apiClient = apiClient;
    }
}

exports.BaseManager = BaseManager;
