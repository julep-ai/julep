# Generation Parameters

Below is a detailed explanation of the request parameters you can use when making API calls to the  Model API. For each parameter, we'll provide a recommendation for both high and low values.

### Request Body Parameters Guide <a href="#request-body-parameters-guide" id="request-body-parameters-guide"></a>

1. **model** (string, Required):
   * Represents the model to be used for the chat conversation.
   * `"julep-ai/samantha-1-turbo"`
2. **messages** (array, Required):
   * Contains the conversation messages exchanged between user, assistant, and system.
   * Each message has a role, content, and optional name and function\_call.
   * Recommendation: Include conversation messages in an array following the provided structure.
3. **functions** (array, Optional):
   * Specifies functions the model can generate JSON inputs for.
   * Each function has a name, description, and parameters.
   * Recommendation: Provide function details if applicable to your conversation.
4. **function\_call** (string or object, Optional):
   * Determines the model's response to function calls.
   * Options: "none" (user response), "auto" (user or function response), or `{"name": "my_function"}` (specific function).
   * Recommendation: Use "none" if no functions are present, "auto" if functions exist, or specify a function.
5. **temperature** (number, Optional):
   * Controls randomness in output. Higher values (e.g., 1.0) make output more random, lower values (e.g., 0.2) make it more focused and deterministic.
   * Range: 0 to 2.
   * Default: 1.
   * Recommendation: High value for creative responses, low value for controlled responses.
6. **top\_p** (number, Optional):
   * Implements nucleus sampling by considering tokens with top\_p probability mass.
   * Higher values (e.g., 0.8) allow more diverse responses, lower values (e.g., 0.2) make responses more focused.
   * Range: 0 to 1.
   * Default: 1.
   * Recommendation: Values around 0.8 maintain coherence with some randomness.
7. **n** (integer, Optional):
   * Specifies the number of response options generated for each input message.
   * Range: Any positive integer.
   * Default: 1.
   * Recommendation: Typically use 1 for most cases.
8. **stream** (boolean, Optional):
   * If true, sends partial message deltas as server-sent events like ChatGPT.
   * Default: false.
9. **stop** (string or array, Optional):
   * Indicates sequences where the API should stop generating tokens.
   * Default: null.
   * Recommendation: Use custom strings to guide response length and depth of content.
10. **max\_tokens** (integer, Optional):
    * Sets the maximum number of tokens generated in a response.
    * Range: Any positive integer.
    * Default: Infinity.
    * Recommendation: Set a specific value to control response length.
11. **presence\_penalty** (number, Optional):
    * Adjusts likelihood of tokens based on their appearance in the conversation.
    * Higher values (e.g., 1.5) encourage introducing new topics, lower values (e.g., -0.5) maintain current context.
    * Range: -2.0 to 2.0.
    * Default: 0.
    * Recommendation: Positive values encourage introducing new topics.
12. **frequency\_penalty** (number, Optional):
    * Adjusts likelihood of tokens based on their frequency in the conversation.
    * Higher values (e.g., 1.5) discourage repetition, lower values (e.g., -0.5) promote more repetition.
    * Range: -2.0 to 2.0.
    * Default: 0.
    * Recommendation: Positive values discourage repetition.
13. **logit\_bias** (map, Optional):
    * Modifies likelihood of specific tokens appearing in the response.
    * Default: null.
    * Recommendation: Use for customizing language or emphasizing certain phrases.
14. **user** (string, Optional):
    * Represents an end-user identifier for monitoring and abuse detection.
    * Default: null.
    * Recommendation: Include a unique user identifier for better context.
