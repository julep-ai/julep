import { JulepApiClient } from "../api/JulepApiClient";

export class BaseManager {
  constructor(public apiClient: JulepApiClient) {}
}
