# JSON Schema $Ref Parser

Parse, Resolve, and Dereference JSON Schema $ref pointers

[![Build Status](https://github.com/readmeio/json-schema-ref-parser/workflows/CI/badge.svg)](https://github.com/readmeio/json-schema-ref-parser/actions)
[![npm](https://img.shields.io/npm/v/@readme/json-schema-ref-parser.svg)](https://www.npmjs.com/package/@readme/json-schema-ref-parser)
[![License](https://img.shields.io/npm/l/@readme/json-schema-ref-parser.svg)](LICENSE)

[![OS and Browser Compatibility](https://apitools.dev/img/badges/ci-badges-with-ie.svg)](https://github.com/readmeio/json-schema-ref-parser/actions)

## The Problem
You've got a JSON Schema with `$ref` pointers to other files and/or URLs.  Maybe you know all the referenced files ahead of time.  Maybe you don't.  Maybe some are local files, and others are remote URLs.  Maybe they are a mix of JSON and YAML format.  Maybe some of the files contain cross-references to each other.

```javascript
{
  "definitions": {
    "person": {
      // references an external file
      "$ref": "schemas/people/Bruce-Wayne.json"
    },
    "place": {
      // references a sub-schema in an external file
      "$ref": "schemas/places.yaml#/definitions/Gotham-City"
    },
    "thing": {
      // references a URL
      "$ref": "http://wayne-enterprises.com/things/batmobile"
    },
    "color": {
      // references a value in an external file via an internal reference
      "$ref": "#/definitions/thing/properties/colors/black-as-the-night"
    }
  }
}
```

## The Solution
JSON Schema $Ref Parser is a full [JSON Reference](https://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03) and [JSON Pointer](https://tools.ietf.org/html/rfc6901) implementation that crawls even the most complex [JSON Schemas](http://json-schema.org/latest/json-schema-core.html) and gives you simple, straightforward JavaScript objects.

- Use **JSON** or **YAML** schemas &mdash; or even a mix of both!
- Supports `$ref` pointers to external files and URLs, as well as [custom sources](https://apitools.dev/json-schema-ref-parser/docs/plugins/resolvers.html) such as databases
- Can [bundle](https://apitools.dev/json-schema-ref-parser/docs/ref-parser.html#bundlepath-options-callback) multiple files into a single schema that only has _internal_ `$ref` pointers
- Can [dereference](https://apitools.dev/json-schema-ref-parser/docs/ref-parser.html#dereferencepath-options-callback) your schema, producing a plain-old JavaScript object that's easy to work with
- Supports [circular references](https://apitools.dev/json-schema-ref-parser/docs/#circular-refs), nested references, back-references, and cross-references between files
- Maintains object reference equality &mdash; `$ref` pointers to the same value always resolve to the same object instance
- Tested in Node v10, v12, & v14, and all major web browsers on Windows, Mac, and Linux


## Example

```javascript
$RefParser.dereference(mySchema, (err, schema) => {
  if (err) {
    console.error(err);
  } else {
    // `schema` is just a normal JavaScript object that contains your entire JSON Schema,
    // including referenced files, combined into a single object
    console.log(schema.definitions.person.properties.firstName);
  }
})
```

Or use `async`/`await` syntax instead. The following example is the same as above:

```javascript
try {
  const schema = await $RefParser.dereference(mySchema);
  console.log(schema.definitions.person.properties.firstName);
} catch(err) {
  console.error(err);
}
```

For more detailed examples, please see the [API Documentation](https://apitools.dev/json-schema-ref-parser/docs/)

## Installation
Install using [npm](https://docs.npmjs.com/about-npm/):

```bash
npm install @readme/json-schema-ref-parser
```

## Usage
When using JSON Schema $Ref Parser in Node.js apps, you'll probably want to use **CommonJS** syntax:

```javascript
const $RefParser = require("@readme/json-schema-ref-parser");
```

When using a transpiler such as [Babel](https://babeljs.io/) or [TypeScript](https://www.typescriptlang.org/), or a bundler such as [Webpack](https://webpack.js.org/) or [Rollup](https://rollupjs.org/), you can use **ECMAScript modules** syntax instead:

```javascript
import $RefParser from "@readme/json-schema-ref-parser";
```

## Differences from `@apidevtools/json-schema-ref-parser`

* Forces YAML to conform to JSON-compatible types. https://github.com/APIDevTools/json-schema-ref-parser/pull/247
* Improved support for OpenAPI 3.1 definitions where `$ref` pointers may live alongside a `description` property. https://github.com/readmeio/json-schema-ref-parser/pull/2
* Exposes a new `$refs.circularRefs` property containing an array of any circular `$ref` pointers that may exist within the schema definition.

## Browser support
JSON Schema $Ref Parser supports recent versions of every major web browser.  Older browsers may require [Babel](https://babeljs.io/) and/or [polyfills](https://babeljs.io/docs/en/next/babel-polyfill).

To use JSON Schema $Ref Parser in a browser, you'll need to use a bundling tool such as [Webpack](https://webpack.js.org/), [Rollup](https://rollupjs.org/), [Parcel](https://parceljs.org/), or [Browserify](http://browserify.org/). Some bundlers may require a bit of configuration, such as setting `browser: true` in [rollup-plugin-resolve](https://github.com/rollup/rollup-plugin-node-resolve).

## API Documentation
Full API documentation is available [right here](https://apitools.dev/json-schema-ref-parser/docs/)

## License
JSON Schema $Ref Parser is 100% free and open-source, under the [MIT license](LICENSE). Use it however you want.

This package is [Treeware](http://treeware.earth). If you use it in production, then we ask that you [**buy the world a tree**](https://plant.treeware.earth/APIDevTools/json-schema-ref-parser) to thank us for our work. By contributing to the Treeware forest you’ll be creating employment for local families and restoring wildlife habitats.
