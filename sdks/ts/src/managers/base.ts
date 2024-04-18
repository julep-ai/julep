import { JulepApiClient } from "../api/JulepApiClient";

/**
 * BaseManager serves as the base class for all manager classes that interact with the Julep API.
 * It provides common functionality needed for API interactions.
 */
export class BaseManager {
  /**
   * Constructs a new instance of BaseManager.
   * @param apiClient The JulepApiClient instance used for API interactions.
   */
  constructor(public apiClient: JulepApiClient) {}
}
