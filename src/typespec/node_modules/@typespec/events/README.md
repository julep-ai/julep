# @typespec/events

TypeSpec library providing events bindings

## Install

```bash
npm install @typespec/events
```

## Decorators

### TypeSpec.Events

- [`@contentType`](#@contenttype)
- [`@data`](#@data)
- [`@events`](#@events)

#### `@contentType`

Specifies the content type of the event envelope, event body, or event payload.
When applied to an event payload, that field must also have a corresponding `@data`
decorator.

```typespec
@TypeSpec.Events.contentType(contentType: valueof string)
```

##### Target

`UnionVariant | ModelProperty`

##### Parameters

| Name        | Type             | Description |
| ----------- | ---------------- | ----------- |
| contentType | `valueof string` |             |

##### Examples

```typespec
@events
union MixedEvents {
  @contentType("application/json")
  message: {
    id: string,
    text: string,
  },
}
```

###### Specify the content type of the event payload.

```typespec
@events
union MixedEvents {
  {
    done: true,
  },
  {
    done: false,
    @data @contentType("text/plain") value: string,
  },
}
```

#### `@data`

Identifies the payload of an event.
Only one field in an event can be marked as the payload.

```typespec
@TypeSpec.Events.data
```

##### Target

`ModelProperty`

##### Parameters

None

##### Examples

```typespec
@events
union MixedEvents {
  {
    metadata: Record<string>,
    @data payload: string,
  },
}
```

#### `@events`

Specify that this union describes a set of events.

```typespec
@TypeSpec.Events.events
```

##### Target

`Union`

##### Parameters

None

##### Examples

```typespec
@events
union MixedEvents {
  pingEvent: string,
  doneEvent: "done",
}
```
