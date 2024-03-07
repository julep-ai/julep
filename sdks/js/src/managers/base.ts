import { JulepApi } from "./types"; // Assuming types are defined elsewhere

/**
 * Base class for all managers.
 */
export class BaseManager {
  /**
   * Creates an instance of BaseManager.
   * @param {JulepApi} apiClient An instance of JulepApi to be used by this class.
   */
  constructor(public apiClient: JulepApi) {}
}
