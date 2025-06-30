# @typespec/rest

TypeSpec REST protocol binding

## Install

```bash
npm install @typespec/rest
```

## Decorators

### TypeSpec.Rest

- [`@action`](#@action)
- [`@actionSeparator`](#@actionseparator)
- [`@autoRoute`](#@autoroute)
- [`@collectionAction`](#@collectionaction)
- [`@copyResourceKeyParameters`](#@copyresourcekeyparameters)
- [`@createsOrReplacesResource`](#@createsorreplacesresource)
- [`@createsOrUpdatesResource`](#@createsorupdatesresource)
- [`@createsResource`](#@createsresource)
- [`@deletesResource`](#@deletesresource)
- [`@listsResource`](#@listsresource)
- [`@parentResource`](#@parentresource)
- [`@readsResource`](#@readsresource)
- [`@resource`](#@resource)
- [`@segment`](#@segment)
- [`@segmentOf`](#@segmentof)
- [`@updatesResource`](#@updatesresource)

#### `@action`

Specify this operation is an action. (Scoped to a resource item /pets/{petId}/my-action)

```typespec
@TypeSpec.Rest.action(name?: valueof string)
```

##### Target

`Operation`

##### Parameters

| Name | Type             | Description                                                                   |
| ---- | ---------------- | ----------------------------------------------------------------------------- |
| name | `valueof string` | Name of the action. If not specified, the name of the operation will be used. |

#### `@actionSeparator`

Defines the separator string that is inserted before the action name in auto-generated routes for actions.

```typespec
@TypeSpec.Rest.actionSeparator(seperator: valueof "/" | ":" | "/:")
```

##### Target

`Model | ModelProperty | Operation`

##### Parameters

| Name      | Type                         | Description                                                      |
| --------- | ---------------------------- | ---------------------------------------------------------------- |
| seperator | `valueof "/" \| ":" \| "/:"` | Seperator seperating the action segment from the rest of the url |

#### `@autoRoute`

This interface or operation should resolve its route automatically. To be used with resource types where the route segments area defined on the models.

```typespec
@TypeSpec.Rest.autoRoute
```

##### Target

`Interface | Operation`

##### Parameters

None

##### Examples

```typespec
@autoRoute
interface Pets {
  get(@segment("pets") @path id: string): void; //-> route: /pets/{id}
}
```

#### `@collectionAction`

Specify this operation is a collection action. (Scopped to a resource, /pets/my-action)

```typespec
@TypeSpec.Rest.collectionAction(resourceType: Model, name?: valueof string)
```

##### Target

`Operation`

##### Parameters

| Name         | Type             | Description                                                                   |
| ------------ | ---------------- | ----------------------------------------------------------------------------- |
| resourceType | `Model`          | Resource marked with                                                          |
| name         | `valueof string` | Name of the action. If not specified, the name of the operation will be used. |

#### `@copyResourceKeyParameters`

Copy the resource key parameters on the model

```typespec
@TypeSpec.Rest.copyResourceKeyParameters(filter?: valueof string)
```

##### Target

`Model`

##### Parameters

| Name   | Type             | Description                           |
| ------ | ---------------- | ------------------------------------- |
| filter | `valueof string` | Filter to exclude certain properties. |

#### `@createsOrReplacesResource`

Specify that this is a CreateOrReplace operation for a given resource.

```typespec
@TypeSpec.Rest.createsOrReplacesResource(resourceType: Model)
```

##### Target

`Operation`

##### Parameters

| Name         | Type    | Description          |
| ------------ | ------- | -------------------- |
| resourceType | `Model` | Resource marked with |

#### `@createsOrUpdatesResource`

Specify that this is a CreatesOrUpdate operation for a given resource.

```typespec
@TypeSpec.Rest.createsOrUpdatesResource(resourceType: Model)
```

##### Target

`Operation`

##### Parameters

| Name         | Type    | Description          |
| ------------ | ------- | -------------------- |
| resourceType | `Model` | Resource marked with |

#### `@createsResource`

Specify that this is a Create operation for a given resource.

```typespec
@TypeSpec.Rest.createsResource(resourceType: Model)
```

##### Target

`Operation`

##### Parameters

| Name         | Type    | Description          |
| ------------ | ------- | -------------------- |
| resourceType | `Model` | Resource marked with |

#### `@deletesResource`

Specify that this is a Delete operation for a given resource.

```typespec
@TypeSpec.Rest.deletesResource(resourceType: Model)
```

##### Target

`Operation`

##### Parameters

| Name         | Type    | Description          |
| ------------ | ------- | -------------------- |
| resourceType | `Model` | Resource marked with |

#### `@listsResource`

Specify that this is a List operation for a given resource.

```typespec
@TypeSpec.Rest.listsResource(resourceType: Model)
```

##### Target

`Operation`

##### Parameters

| Name         | Type    | Description          |
| ------------ | ------- | -------------------- |
| resourceType | `Model` | Resource marked with |

#### `@parentResource`

Mark model as a child of the given parent resource.

```typespec
@TypeSpec.Rest.parentResource(parent: Model)
```

##### Target

`Model`

##### Parameters

| Name   | Type    | Description   |
| ------ | ------- | ------------- |
| parent | `Model` | Parent model. |

#### `@readsResource`

Specify that this is a Read operation for a given resource.

```typespec
@TypeSpec.Rest.readsResource(resourceType: Model)
```

##### Target

`Operation`

##### Parameters

| Name         | Type    | Description          |
| ------------ | ------- | -------------------- |
| resourceType | `Model` | Resource marked with |

#### `@resource`

Mark this model as a resource type with a name.

```typespec
@TypeSpec.Rest.resource(collectionName: valueof string)
```

##### Target

`Model`

##### Parameters

| Name           | Type             | Description            |
| -------------- | ---------------- | ---------------------- |
| collectionName | `valueof string` | type's collection name |

#### `@segment`

Defines the preceding path segment for a

```typespec
@TypeSpec.Rest.segment(name: valueof string)
```

##### Target

`Model | ModelProperty | Operation`

##### Parameters

| Name | Type             | Description                                                                                    |
| ---- | ---------------- | ---------------------------------------------------------------------------------------------- |
| name | `valueof string` | Segment that will be inserted into the operation route before the path parameter's name field. |

##### Examples

#### `@segmentOf`

Returns the URL segment of a given model if it has `@segment` and `@key` decorator.

```typespec
@TypeSpec.Rest.segmentOf(type: Model)
```

##### Target

`Operation`

##### Parameters

| Name | Type    | Description  |
| ---- | ------- | ------------ |
| type | `Model` | Target model |

#### `@updatesResource`

Specify that this is a Update operation for a given resource.

```typespec
@TypeSpec.Rest.updatesResource(resourceType: Model)
```

##### Target

`Operation`

##### Parameters

| Name         | Type    | Description          |
| ------------ | ------- | -------------------- |
| resourceType | `Model` | Resource marked with |
