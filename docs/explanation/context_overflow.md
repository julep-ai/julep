# Context Overflow Handling in Julep

Julep provides mechanisms to handle scenarios where the context size grows beyond the `token_budget` or the model's input limit. The behavior is determined by the `context_overflow` setting:

1. `null` (default): 
   - Raises an exception
   - The client is responsible for creating a new session or clearing the history for the current one

2. `"truncate"`: 
   - Truncates the context from the top, except for the system prompt
   - Continues truncating until the size falls below the budget
   - Raises an error if the system prompt and last message combined exceed the budget

3. `"adaptive"`: 
   - When the context size reaches 75% of the `token_budget`, a background task is created
   - This task compresses the information by summarizing, merging, and clipping messages in the context
   - Operates on a best-effort basis
   - Requests might fail if the context wasn't compressed enough or on time

By offering these options, Julep allows developers to choose the most appropriate strategy for handling context overflow in their applications, balancing between maintaining conversation history and staying within model limits.