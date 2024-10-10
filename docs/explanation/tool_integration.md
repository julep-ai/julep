# Tool Integration in Julep

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


Julep provides a flexible system for integrating various types of tools that agents can use during interactions. These tools enable agents to perform actions, retrieve information, or interact with external systems.

## Types of Tools

1. **User-defined Functions**
   - Function signatures that you provide to the model
   - Similar to OpenAI's function-calling feature
   - Example:
     ```yaml
     name: send_text_message
     description: Send a text message to a recipient.
     parameters:
       type: object
       properties:
         to:
           type: string
           description: Phone number of recipient.
         text:
           type: string
           description: Content of the message.
     ```

2. **System Tools** (upcoming)
   - Built-in tools for calling Julep APIs
   - Can trigger task executions, append to metadata fields, etc.
   - Executed automatically when needed, no client-side action required

3. **Built-in Integrations** (upcoming)
   - Integrated third-party tools from providers like composio and anon
   - Support planned for various langchain toolkits (Github, Gitlab, Gmail, Jira, MultiOn, Slack)
   - Executed directly on the Julep backend
   - Additional runtime parameters can be set in agent/session/user metadata

4. **Webhooks & API Calls** (upcoming)
   - Julep can build natural-language tools from OpenAPI specs
   - Uses langchain's NLA toolkit under the hood
   - Additional runtime parameters loaded from metadata fields

## Partial Application of Arguments

Julep allows for partial application of arguments to tools using the `x-tool-parameters` field in metadata. This is useful for fixing certain parameters for a tool. Example:

```json
{
  "metadata": {
    "x-tool-parameters": {
      "function:check_account_status": {
        "customer_id": 42
      }
    }
  }
}
```

## Resolving Parameters with the Same Name

When multiple scopes (user, agent, session) define the same parameter, Julep follows a precedence order:

1. Session
2. User
3. Agent

This allows for flexible configuration of tools across different scopes while maintaining clear rules for parameter resolution.

By providing these various tool integration options and configuration capabilities, Julep enables the creation of powerful and flexible agent-based applications that can interact with a wide range of external systems and data sources.