Swagger Methods
============================
#### HTTP methods that are supported by Swagger 2.0

[![Cross-Platform Compatibility](https://apitools.dev/img/badges/os-badges.svg)](https://github.com/APIDevTools/swagger-methods/actions)
[![Build Status](https://github.com/APIDevTools/swagger-methods/workflows/CI-CD/badge.svg)](https://github.com/APIDevTools/swagger-methods/actions)

[![Coverage Status](https://coveralls.io/repos/github/APIDevTools/swagger-methods/badge.svg?branch=master)](https://coveralls.io/github/APIDevTools/swagger-methods?branch=master)
[![Dependencies](https://david-dm.org/APIDevTools/swagger-methods.svg)](https://david-dm.org/APIDevTools/swagger-methods)

[![npm](https://img.shields.io/npm/v/@apidevtools/swagger-methods.svg?branch=master)](https://www.npmjs.com/package/@apidevtools/swagger-methods)
[![License](https://img.shields.io/npm/l/@apidevtools/swagger-methods.svg)](LICENSE)
[![Buy us a tree](https://img.shields.io/badge/Treeware-%F0%9F%8C%B3-lightgreen)](https://plant.treeware.earth/APIDevTools/swagger-methods)

This is an array of lower-case HTTP method names that are supported by the [Swagger 2.0 spec](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md).

This module is [tested](test/index.spec.js) against the [Swagger 2.0 schema](https://www.npmjs.com/package/swagger-schema-official)


Installation
--------------------------
Install using [npm](https://docs.npmjs.com/about-npm/):

```bash
npm install @apidevtools/swagger-methods
```



Usage
--------------------------

```javascript
var methods = require('@apidevtools/swagger-methods');

methods.forEach(function(method) {
  console.log(method);
});

// get
// put
// post
// delete
// options
// head
// patch
```



Contributing
--------------------------
I welcome any contributions, enhancements, and bug-fixes.  [Open an issue](https://github.com/APIDevTools/swagger-methods/issues) on GitHub and [submit a pull request](https://github.com/APIDevTools/swagger-methods/pulls).

#### Building/Testing
To build/test the project locally on your computer:

1. **Clone this repo**<br>
`git clone https://github.com/APIDevTools/swagger-methods.git`

2. **Install dev dependencies**<br>
`npm install`

3. **Run the unit tests**<br>
`npm test`



License
--------------------------
[MIT license](LICENSE). Use it however you want.

This package is [Treeware](http://treeware.earth). If you use it in production, then we ask that you [**buy the world a tree**](https://plant.treeware.earth/APIDevTools/swagger-methods) to thank us for our work. By contributing to the Treeware forest you’ll be creating employment for local families and restoring wildlife habitats.



Big Thanks To
--------------------------
Thanks to these awesome companies for their support of Open Source developers ❤

[![Travis CI](https://jstools.dev/img/badges/travis-ci.svg)](https://travis-ci.com)
[![SauceLabs](https://jstools.dev/img/badges/sauce-labs.svg)](https://saucelabs.com)
[![Coveralls](https://jstools.dev/img/badges/coveralls.svg)](https://coveralls.io)
