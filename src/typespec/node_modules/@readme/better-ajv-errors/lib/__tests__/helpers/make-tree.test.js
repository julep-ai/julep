"use strict";

var _helpers = require("../../helpers");
describe('makeTree', function () {
  it('works on empty array', function () {
    expect((0, _helpers.makeTree)([])).toMatchInlineSnapshot("\n      {\n        \"children\": {},\n      }\n    ");
  });
  it('works on root dataPath', function () {
    expect((0, _helpers.makeTree)([{
      dataPath: ''
    }])).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"\": {\n            \"children\": {},\n            \"errors\": [\n              {\n                \"dataPath\": \"\",\n              },\n            ],\n          },\n        },\n      }\n    ");
  });
  it('works on nested dataPath', function () {
    expect((0, _helpers.makeTree)([{
      dataPath: '/root/child'
    }])).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"/root\": {\n            \"children\": {\n              \"/child\": {\n                \"children\": {},\n                \"errors\": [\n                  {\n                    \"dataPath\": \"/root/child\",\n                  },\n                ],\n              },\n            },\n            \"errors\": [],\n          },\n        },\n      }\n    ");
  });
  it('works on array dataPath', function () {
    expect((0, _helpers.makeTree)([{
      dataPath: '/root/child/0'
    }, {
      dataPath: '/root/child/1'
    }])).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"/root\": {\n            \"children\": {\n              \"/child/0\": {\n                \"children\": {},\n                \"errors\": [\n                  {\n                    \"dataPath\": \"/root/child/0\",\n                  },\n                ],\n              },\n              \"/child/1\": {\n                \"children\": {},\n                \"errors\": [\n                  {\n                    \"dataPath\": \"/root/child/1\",\n                  },\n                ],\n              },\n            },\n            \"errors\": [],\n          },\n        },\n      }\n    ");
  });
  it('works on array item dataPath', function () {
    expect((0, _helpers.makeTree)([{
      dataPath: '/root/child/0/grand-child'
    }, {
      dataPath: '/root/child/1/grand-child'
    }])).toMatchInlineSnapshot("\n      {\n        \"children\": {\n          \"/root\": {\n            \"children\": {\n              \"/child/0\": {\n                \"children\": {\n                  \"/grand-child\": {\n                    \"children\": {},\n                    \"errors\": [\n                      {\n                        \"dataPath\": \"/root/child/0/grand-child\",\n                      },\n                    ],\n                  },\n                },\n                \"errors\": [],\n              },\n              \"/child/1\": {\n                \"children\": {\n                  \"/grand-child\": {\n                    \"children\": {},\n                    \"errors\": [\n                      {\n                        \"dataPath\": \"/root/child/1/grand-child\",\n                      },\n                    ],\n                  },\n                },\n                \"errors\": [],\n              },\n            },\n            \"errors\": [],\n          },\n        },\n      }\n    ");
  });
});