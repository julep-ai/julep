"use strict";

var _helpers = require("../../helpers");
describe('filterRedundantErrors', function () {
  it('should prioritize required', function () {
    var tree = {
      children: {
        a: {
          children: {
            b: {
              children: {},
              errors: [{
                keyword: 'required'
              }]
            }
          },
          errors: [{
            keyword: 'required'
          }, {
            keyword: 'anyOf'
          }, {
            keyword: 'enum'
          }]
        }
      }
    };
    (0, _helpers.filterRedundantErrors)(tree);
    expect(tree).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"a\": {\n            \"children\": {},\n            \"errors\": [\n              {\n                \"keyword\": \"required\",\n              },\n            ],\n          },\n        },\n      }\n    ");
  });
  it('should handle anyOf', function () {
    var tree = {
      children: {
        a: {
          children: {
            b: {
              children: {},
              errors: [{
                keyword: 'required'
              }]
            }
          },
          errors: [{
            keyword: 'anyOf'
          }, {
            keyword: 'enum'
          }]
        }
      }
    };
    (0, _helpers.filterRedundantErrors)(tree);
    expect(tree).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"a\": {\n            \"children\": {\n              \"b\": {\n                \"children\": {},\n                \"errors\": [\n                  {\n                    \"keyword\": \"required\",\n                  },\n                ],\n              },\n            },\n          },\n        },\n      }\n    ");
  });
  it('should handle enum', function () {
    var tree = {
      children: {
        a: {
          children: {
            b: {
              children: {},
              errors: [{
                keyword: 'enum'
              }, {
                keyword: 'enum'
              }]
            }
          },
          errors: [{
            keyword: 'anyOf'
          }, {
            keyword: 'additionalProperty'
          }]
        }
      }
    };
    (0, _helpers.filterRedundantErrors)(tree);
    expect(tree).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"a\": {\n            \"children\": {\n              \"b\": {\n                \"children\": {},\n                \"errors\": [\n                  {\n                    \"keyword\": \"enum\",\n                  },\n                  {\n                    \"keyword\": \"enum\",\n                  },\n                ],\n              },\n            },\n          },\n        },\n      }\n    ");
  });
  it('should handle enum - sibling', function () {
    var tree = {
      children: {
        a1: {
          children: {},
          errors: [{
            keyword: 'enum'
          }, {
            keyword: 'enum'
          }]
        },
        a2: {
          children: {},
          errors: [{
            keyword: 'additionalProperty'
          }]
        }
      }
    };
    (0, _helpers.filterRedundantErrors)(tree);
    expect(tree).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"a2\": {\n            \"children\": {},\n            \"errors\": [\n              {\n                \"keyword\": \"additionalProperty\",\n              },\n            ],\n          },\n        },\n      }\n    ");
  });
  it('should handle enum - sibling with nested error', function () {
    var tree = {
      children: {
        a1: {
          children: {
            b1: {
              children: {},
              errors: [{
                keyword: 'additionalProperty'
              }]
            }
          },
          errors: []
        },
        a2: {
          children: {},
          errors: [{
            keyword: 'enum'
          }, {
            keyword: 'enum'
          }]
        }
      }
    };
    (0, _helpers.filterRedundantErrors)(tree);
    expect(tree).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"a1\": {\n            \"children\": {\n              \"b1\": {\n                \"children\": {},\n                \"errors\": [\n                  {\n                    \"keyword\": \"additionalProperty\",\n                  },\n                ],\n              },\n            },\n            \"errors\": [],\n          },\n        },\n      }\n    ");
  });
  it('should not remove anyOf errors if there are no children', function () {
    var tree = {
      children: {
        '/object': {
          children: {
            '/type': {
              children: {},
              errors: [{
                keyword: 'type'
              }, {
                keyword: 'type'
              }, {
                keyword: 'anyOf'
              }]
            }
          },
          errors: []
        }
      }
    };
    (0, _helpers.filterRedundantErrors)(tree);
    expect(tree).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"/object\": {\n            \"children\": {\n              \"/type\": {\n                \"children\": {},\n                \"errors\": [\n                  {\n                    \"keyword\": \"type\",\n                  },\n                  {\n                    \"keyword\": \"type\",\n                  },\n                  {\n                    \"keyword\": \"anyOf\",\n                  },\n                ],\n              },\n            },\n            \"errors\": [],\n          },\n        },\n      }\n    ");
  });
});