[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$CreateAgentRequest

# Module: api/schemas/$CreateAgentRequest

## Table of contents

### Variables

- [$CreateAgentRequest](api_schemas__CreateAgentRequest.md#$createagentrequest)

## Variables

### $CreateAgentRequest

• `Const` **$CreateAgentRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for creating an agent"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } ; `default_settings`: \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } ; `docs`: \{ `contains`: \{ `type`: ``"CreateDoc"`` = "CreateDoc" } ; `type`: ``"array"`` = "array" } ; `instructions`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } ; `model`: \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `tools`: \{ `contains`: \{ `type`: ``"CreateToolRequest"`` = "CreateToolRequest" } ; `type`: ``"array"`` = "array" }  } |
| `properties.about` | \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the agent"`` |
| `properties.about.type` | ``"string"`` |
| `properties.default_settings` | \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } |
| `properties.default_settings.description` | ``"Default model settings to start every session with"`` |
| `properties.default_settings.type` | ``"AgentDefaultSettings"`` |
| `properties.docs` | \{ `contains`: \{ `type`: ``"CreateDoc"`` = "CreateDoc" } ; `type`: ``"array"`` = "array" } |
| `properties.docs.contains` | \{ `type`: ``"CreateDoc"`` = "CreateDoc" } |
| `properties.docs.contains.type` | ``"CreateDoc"`` |
| `properties.docs.type` | ``"array"`` |
| `properties.instructions` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.instructions.contains` | readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.instructions.description` | ``"Instructions for the agent"`` |
| `properties.instructions.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"(Optional) metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.model` | \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } |
| `properties.model.description` | ``"Name of the model that the agent is supposed to use"`` |
| `properties.model.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the agent"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |
| `properties.tools` | \{ `contains`: \{ `type`: ``"CreateToolRequest"`` = "CreateToolRequest" } ; `type`: ``"array"`` = "array" } |
| `properties.tools.contains` | \{ `type`: ``"CreateToolRequest"`` = "CreateToolRequest" } |
| `properties.tools.contains.type` | ``"CreateToolRequest"`` |
| `properties.tools.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$CreateAgentRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$CreateAgentRequest.ts#L5)
