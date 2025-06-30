# @typespec/streams

TypeSpec library providing stream bindings

## Install

```bash
npm install @typespec/streams
```

## Decorators

### TypeSpec.Streams

- [`@streamOf`](#@streamof)

#### `@streamOf`

Specify that a model represents a stream protocol type whose data is described
by `Type`.

```typespec
@TypeSpec.Streams.streamOf(type: unknown)
```

##### Target

`Model`

##### Parameters

| Name | Type      | Description                                             |
| ---- | --------- | ------------------------------------------------------- |
| type | `unknown` | The type that models the underlying data of the stream. |

##### Examples

```typespec
model Message {
  id: string;
  text: string;
}

@streamOf(Message)
model Response {
  @body body: string;
}
```
