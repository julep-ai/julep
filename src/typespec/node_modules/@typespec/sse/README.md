# @typespec/sse

TypeSpec library providing server sent events bindings

## Install

```bash
npm install @typespec/sse
```

## Decorators

### TypeSpec.SSE

- [`@terminalEvent`](#@terminalevent)

#### `@terminalEvent`

Indicates that the presence of this event is a terminal event,
and the client should disconnect from the server.

```typespec
@TypeSpec.SSE.terminalEvent
```

##### Target

`UnionVariant`

##### Parameters

None
