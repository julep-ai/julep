"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
var _regenerator = _interopRequireDefault(require("@babel/runtime/regenerator"));
var _slicedToArray2 = _interopRequireDefault(require("@babel/runtime/helpers/slicedToArray"));
var _asyncToGenerator2 = _interopRequireDefault(require("@babel/runtime/helpers/asyncToGenerator"));
var _momoa = require("@humanwhocodes/momoa");
var _testHelpers = require("../../test-helpers");
var _required = _interopRequireDefault(require("../required"));
describe('Required', function () {
  it.each([['prints correctly for missing required prop', true], ['prints correctly for missing required prop[without colors]', false]])('%s', /*#__PURE__*/function () {
    var _ref = (0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee(_, colorize) {
      var _yield$getSchemaAndDa, _yield$getSchemaAndDa2, schema, data, jsonRaw, jsonAst, error;
      return _regenerator["default"].wrap(function _callee$(_context) {
        while (1) {
          switch (_context.prev = _context.next) {
            case 0:
              _context.next = 2;
              return (0, _testHelpers.getSchemaAndData)('required', __dirname);
            case 2:
              _yield$getSchemaAndDa = _context.sent;
              _yield$getSchemaAndDa2 = (0, _slicedToArray2["default"])(_yield$getSchemaAndDa, 2);
              schema = _yield$getSchemaAndDa2[0];
              data = _yield$getSchemaAndDa2[1];
              jsonRaw = JSON.stringify(data, null, 2);
              jsonAst = (0, _momoa.parse)(jsonRaw);
              error = new _required["default"]({
                keyword: 'required',
                dataPath: '/nested',
                schemaPath: '#/required',
                params: {
                  missingProperty: 'id'
                },
                message: "should have required property 'id'"
              }, {
                colorize: colorize,
                data: data,
                schema: schema,
                jsonRaw: jsonRaw,
                jsonAst: jsonAst
              });
              expect(error.print()).toMatchSnapshot();
            case 10:
            case "end":
              return _context.stop();
          }
        }
      }, _callee);
    }));
    return function (_x, _x2) {
      return _ref.apply(this, arguments);
    };
  }());
});