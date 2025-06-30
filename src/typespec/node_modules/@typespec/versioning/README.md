# @typespec/versioning

TypeSpec library for declaring and emitting versioned APIs

## Install

```bash
npm install @typespec/versioning
```

## Usage

### Consuming versioning library from an emitter

#### Get the service representation at a given version

Versioning library works with projection to project the service at a given version.

```ts
// Get a list of all the different version of the service and the projections
const projections = buildVersionProjections(program, serviceNamespace);

for (const projection of projections) {
  const projectedProgram = projectProgram(program, projection.projections);
  // projectedProgram now contains the representation of the service at the given version.
}
```

#### Get list of versions and version dependency across namespaces

Versioning library works with projection to project the service at a given version.

```ts
const versions = resolveVersions(program, serviceNamespace);
// versions now contain a list of all the version of the service namespace and what version should all the other dependencies namespace use.
```

#### Consume versioning manually

If the emitter needs to have the whole picture of the service evolution across the version then using the decorator accessor will provide the metadata for each type:

- `getAddedOn`
- `getRemovedOn`
- `getRenamedFromVersion`
- `getMadeOptionalOn`

## Decorators

### TypeSpec.Versioning

- [`@added`](#@added)
- [`@madeOptional`](#@madeoptional)
- [`@madeRequired`](#@maderequired)
- [`@removed`](#@removed)
- [`@renamedFrom`](#@renamedfrom)
- [`@returnTypeChangedFrom`](#@returntypechangedfrom)
- [`@typeChangedFrom`](#@typechangedfrom)
- [`@useDependency`](#@usedependency)
- [`@versioned`](#@versioned)

#### `@added`

Identifies when the target was added.

```typespec
@TypeSpec.Versioning.added(version: EnumMember)
```

##### Target

`Model | ModelProperty | Operation | Enum | EnumMember | Union | UnionVariant | Scalar | Interface`

##### Parameters

| Name    | Type         | Description                               |
| ------- | ------------ | ----------------------------------------- |
| version | `EnumMember` | The version that the target was added in. |

##### Examples

```tsp
@added(Versions.v2)
op addedInV2(): void;

@added(Versions.v2)
model AlsoAddedInV2 {}

model Foo {
  name: string;

  @added(Versions.v3)
  addedInV3: string;
}
```

#### `@madeOptional`

Identifies when a target was made optional.

```typespec
@TypeSpec.Versioning.madeOptional(version: EnumMember)
```

##### Target

`ModelProperty`

##### Parameters

| Name    | Type         | Description                                       |
| ------- | ------------ | ------------------------------------------------- |
| version | `EnumMember` | The version that the target was made optional in. |

##### Examples

```tsp
model Foo {
  name: string;

  @madeOptional(Versions.v2)
  nickname?: string;
}
```

#### `@madeRequired`

Identifies when a target was made required.

```typespec
@TypeSpec.Versioning.madeRequired(version: EnumMember)
```

##### Target

`ModelProperty`

##### Parameters

| Name    | Type         | Description                                       |
| ------- | ------------ | ------------------------------------------------- |
| version | `EnumMember` | The version that the target was made required in. |

##### Examples

```tsp
model Foo {
  name: string;

  @madeRequired(Versions.v2)
  nickname: string;
}
```

#### `@removed`

Identifies when the target was removed.

```typespec
@TypeSpec.Versioning.removed(version: EnumMember)
```

##### Target

`Model | ModelProperty | Operation | Enum | EnumMember | Union | UnionVariant | Scalar | Interface`

##### Parameters

| Name    | Type         | Description                                 |
| ------- | ------------ | ------------------------------------------- |
| version | `EnumMember` | The version that the target was removed in. |

##### Examples

```tsp
@removed(Versions.v2)
op removedInV2(): void;

@removed(Versions.v2)
model AlsoRemovedInV2 {}

model Foo {
  name: string;

  @removed(Versions.v3)
  removedInV3: string;
}
```

#### `@renamedFrom`

Identifies when the target has been renamed.

```typespec
@TypeSpec.Versioning.renamedFrom(version: EnumMember, oldName: valueof string)
```

##### Target

`Model | ModelProperty | Operation | Enum | EnumMember | Union | UnionVariant | Scalar | Interface`

##### Parameters

| Name    | Type             | Description                                 |
| ------- | ---------------- | ------------------------------------------- |
| version | `EnumMember`     | The version that the target was renamed in. |
| oldName | `valueof string` | The previous name of the target.            |

##### Examples

```tsp
@renamedFrom(Versions.v2, "oldName")
op newName(): void;
```

#### `@returnTypeChangedFrom`

Identifies when the target type changed.

```typespec
@TypeSpec.Versioning.returnTypeChangedFrom(version: EnumMember, oldType: unknown)
```

##### Target

`Operation`

##### Parameters

| Name    | Type         | Description                                  |
| ------- | ------------ | -------------------------------------------- |
| version | `EnumMember` | The version that the target type changed in. |
| oldType | `unknown`    | The previous type of the target.             |

#### `@typeChangedFrom`

Identifies when the target type changed.

```typespec
@TypeSpec.Versioning.typeChangedFrom(version: EnumMember, oldType: unknown)
```

##### Target

`ModelProperty`

##### Parameters

| Name    | Type         | Description                                  |
| ------- | ------------ | -------------------------------------------- |
| version | `EnumMember` | The version that the target type changed in. |
| oldType | `unknown`    | The previous type of the target.             |

#### `@useDependency`

Identifies that a namespace or a given versioning enum member relies upon a versioned package.

```typespec
@TypeSpec.Versioning.useDependency(...versionRecords: EnumMember[])
```

##### Target

`EnumMember | Namespace`

##### Parameters

| Name           | Type           | Description                                                           |
| -------------- | -------------- | --------------------------------------------------------------------- |
| versionRecords | `EnumMember[]` | The dependent library version(s) for the target namespace or version. |

##### Examples

###### Select a single version of `MyLib` to use

```tsp
@useDependency(MyLib.Versions.v1_1)
namespace NonVersionedService;
```

###### Select which version of the library match to which version of the service.

```tsp
@versioned(Versions)
namespace MyService1;
enum Version {
  @useDependency(MyLib.Versions.v1_1) // V1 use lib v1_1
  v1,
  @useDependency(MyLib.Versions.v1_1) // V2 use lib v1_1
  v2,
  @useDependency(MyLib.Versions.v2) // V3 use lib v2
  v3,
}
```

#### `@versioned`

Identifies that the decorated namespace is versioned by the provided enum.

```typespec
@TypeSpec.Versioning.versioned(versions: Enum)
```

##### Target

`Namespace`

##### Parameters

| Name     | Type   | Description                                     |
| -------- | ------ | ----------------------------------------------- |
| versions | `Enum` | The enum that describes the supported versions. |

##### Examples

```tsp
@versioned(Versions)
namespace MyService;
enum Versions {
  v1,
  v2,
  v3,
}
```
