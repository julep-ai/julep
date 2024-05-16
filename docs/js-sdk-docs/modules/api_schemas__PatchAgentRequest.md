[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$PatchAgentRequest

# Module: api/schemas/$PatchAgentRequest

## Table of contents

### Variables

- [$PatchAgentRequest](api_schemas__PatchAgentRequest.md#$patchagentrequest)

## Variables

### $PatchAgentRequest

• `Const` **$PatchAgentRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A request for patching an agent"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } ; `default_settings`: \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } ; `instructions`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `model`: \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the agent"`` ; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the agent"`` |
| `properties.about.type` | ``"string"`` |
| `properties.default_settings` | \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } |
| `properties.default_settings.description` | ``"Default model settings to start every session with"`` |
| `properties.default_settings.type` | ``"AgentDefaultSettings"`` |
| `properties.instructions` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.instructions.contains` | readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.instructions.description` | ``"Instructions for the agent"`` |
| `properties.instructions.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.model` | \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } |
| `properties.model.description` | ``"Name of the model that the agent is supposed to use"`` |
| `properties.model.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the agent"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the agent"`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$PatchAgentRequest.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$PatchAgentRequest.ts#L5)
