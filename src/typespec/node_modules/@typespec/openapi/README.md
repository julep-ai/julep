# @typespec/openapi

TypeSpec library providing OpenAPI concepts

## Install

```bash
npm install @typespec/openapi
```

## Decorators

### TypeSpec.OpenAPI

- [`@defaultResponse`](#@defaultresponse)
- [`@extension`](#@extension)
- [`@externalDocs`](#@externaldocs)
- [`@info`](#@info)
- [`@operationId`](#@operationid)

#### `@defaultResponse`

Specify that this model is to be treated as the OpenAPI `default` response.
This differs from the compiler built-in `@error` decorator as this does not necessarily represent an error.

```typespec
@TypeSpec.OpenAPI.defaultResponse
```

##### Target

`Model`

##### Parameters

None

##### Examples

```typespec
@defaultResponse
model PetStoreResponse is object;

op listPets(): Pet[] | PetStoreResponse;
```

#### `@extension`

Attach some custom data to the OpenAPI element generated from this type.

```typespec
@TypeSpec.OpenAPI.extension(key: valueof string, value: unknown)
```

##### Target

`unknown`

##### Parameters

| Name  | Type             | Description                         |
| ----- | ---------------- | ----------------------------------- |
| key   | `valueof string` | Extension key. Must start with `x-` |
| value | `unknown`        | Extension value.                    |

##### Examples

```typespec
@extension("x-custom", "My value")
@extension(
  "x-pageable",
  {
    nextLink: "x-next-link",
  }
)
op read(): string;
```

#### `@externalDocs`

Specify the OpenAPI `externalDocs` property for this type.

```typespec
@TypeSpec.OpenAPI.externalDocs(url: valueof string, description?: valueof string)
```

##### Target

`unknown`

##### Parameters

| Name        | Type             | Description             |
| ----------- | ---------------- | ----------------------- |
| url         | `valueof string` | Url to the docs         |
| description | `valueof string` | Description of the docs |

##### Examples

```typespec
@externalDocs(
  "https://example.com/detailed.md",
  "Detailed information on how to use this operation"
)
op listPets(): Pet[];
```

#### `@info`

Specify OpenAPI additional information.
The service `title` and `version` are already specified using `@service`.

```typespec
@TypeSpec.OpenAPI.info(additionalInfo: TypeSpec.OpenAPI.AdditionalInfo)
```

##### Target

`Namespace`

##### Parameters

| Name           | Type                                | Description            |
| -------------- | ----------------------------------- | ---------------------- |
| additionalInfo | [`AdditionalInfo`](#additionalinfo) | Additional information |

#### `@operationId`

Specify the OpenAPI `operationId` property for this operation.

```typespec
@TypeSpec.OpenAPI.operationId(operationId: valueof string)
```

##### Target

`Operation`

##### Parameters

| Name        | Type             | Description         |
| ----------- | ---------------- | ------------------- |
| operationId | `valueof string` | Operation id value. |

##### Examples

```typespec
@operationId("download")
op read(): string;
```
