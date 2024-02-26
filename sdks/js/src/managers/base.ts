import { JulepApi } from "../client";

// Purpose: Base class for all managers
class BaseManager {
    /**
     * A class that serves as a base manager for working with different API clients.
     */
    api_client: JulepApi;

    constructor(api_client: JulepApi) {
        /**
         * Constructor for the class that initializes it with an API client.
         * @param api_client An instance of JulepApi to be used by this class.
         */
        this.api_client = api_client;
    }
}