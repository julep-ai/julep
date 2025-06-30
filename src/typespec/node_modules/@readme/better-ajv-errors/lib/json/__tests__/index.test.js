"use strict";

var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");
var _regenerator = _interopRequireDefault(require("@babel/runtime/regenerator"));
var _asyncToGenerator2 = _interopRequireDefault(require("@babel/runtime/helpers/asyncToGenerator"));
var _fs = require("fs");
var _momoa = require("@humanwhocodes/momoa");
var _jestFixtures = require("jest-fixtures");
var _ = require("..");
function loadScenario(_x) {
  return _loadScenario.apply(this, arguments);
}
function _loadScenario() {
  _loadScenario = (0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee8(n) {
    var fixturePath;
    return _regenerator["default"].wrap(function _callee8$(_context8) {
      while (1) {
        switch (_context8.prev = _context8.next) {
          case 0:
            _context8.next = 2;
            return (0, _jestFixtures.getFixturePath)(__dirname, "scenario-".concat(n, ".json"));
          case 2:
            fixturePath = _context8.sent;
            return _context8.abrupt("return", (0, _momoa.parse)((0, _fs.readFileSync)(fixturePath, 'utf8')));
          case 4:
          case "end":
            return _context8.stop();
        }
      }
    }, _callee8);
  }));
  return _loadScenario.apply(this, arguments);
}
describe('JSON', function () {
  it('can work on simple JSON', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee() {
    var jsonAst;
    return _regenerator["default"].wrap(function _callee$(_context) {
      while (1) {
        switch (_context.prev = _context.next) {
          case 0:
            _context.next = 2;
            return loadScenario(1);
          case 2:
            jsonAst = _context.sent;
            expect((0, _.getMetaFromPath)(jsonAst, '/foo')).toMatchSnapshot();
            expect((0, _.getMetaFromPath)(jsonAst, '/foo', true)).toMatchSnapshot();
          case 5:
          case "end":
            return _context.stop();
        }
      }
    }, _callee);
  })));
  it('can work on JSON with a key named value', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee2() {
    var jsonAst;
    return _regenerator["default"].wrap(function _callee2$(_context2) {
      while (1) {
        switch (_context2.prev = _context2.next) {
          case 0:
            _context2.next = 2;
            return loadScenario(2);
          case 2:
            jsonAst = _context2.sent;
            expect((0, _.getMetaFromPath)(jsonAst, '/value')).toMatchSnapshot();
            expect((0, _.getMetaFromPath)(jsonAst, '/value', true)).toMatchSnapshot();
          case 5:
          case "end":
            return _context2.stop();
        }
      }
    }, _callee2);
  })));
  it('can work on JSON with a key named meta', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee3() {
    var jsonAst;
    return _regenerator["default"].wrap(function _callee3$(_context3) {
      while (1) {
        switch (_context3.prev = _context3.next) {
          case 0:
            _context3.next = 2;
            return loadScenario(3);
          case 2:
            jsonAst = _context3.sent;
            expect((0, _.getMetaFromPath)(jsonAst, '/meta/isMeta')).toMatchSnapshot();
            expect((0, _.getMetaFromPath)(jsonAst, '/meta/isMeta', true)).toMatchSnapshot();
          case 5:
          case "end":
            return _context3.stop();
        }
      }
    }, _callee3);
  })));
  it('can work on JSON with Array', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee4() {
    var jsonAst;
    return _regenerator["default"].wrap(function _callee4$(_context4) {
      while (1) {
        switch (_context4.prev = _context4.next) {
          case 0:
            _context4.next = 2;
            return loadScenario(4);
          case 2:
            jsonAst = _context4.sent;
            expect((0, _.getMetaFromPath)(jsonAst, '/arr/1/foo')).toMatchSnapshot();
            expect((0, _.getMetaFromPath)(jsonAst, '/arr/1/foo', true)).toMatchSnapshot();
          case 5:
          case "end":
            return _context4.stop();
        }
      }
    }, _callee4);
  })));
  it('can work on JSON with Array with empty children', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee5() {
    var jsonAst;
    return _regenerator["default"].wrap(function _callee5$(_context5) {
      while (1) {
        switch (_context5.prev = _context5.next) {
          case 0:
            _context5.next = 2;
            return loadScenario(4);
          case 2:
            jsonAst = _context5.sent;
            expect((0, _.getDecoratedDataPath)(jsonAst, '/arr/4')).toMatchSnapshot();
          case 4:
          case "end":
            return _context5.stop();
        }
      }
    }, _callee5);
  })));
  it('should not throw error when children is array', function () {
    var rawJsonWithArrayItem = JSON.stringify({
      foo: 'bar',
      arr: [1, {
        foo: 'bar'
      }, 3, ['anArray']]
    });
    var jsonAst = (0, _momoa.parse)(rawJsonWithArrayItem);
    expect((0, _.getDecoratedDataPath)(jsonAst, '/arr/3')).toMatchSnapshot();
  });
  it('can work with unescaped JSON pointers with ~1', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee6() {
    var jsonAst;
    return _regenerator["default"].wrap(function _callee6$(_context6) {
      while (1) {
        switch (_context6.prev = _context6.next) {
          case 0:
            _context6.next = 2;
            return loadScenario(5);
          case 2:
            jsonAst = _context6.sent;
            expect((0, _.getMetaFromPath)(jsonAst, '/foo/~1some~1path/value')).toMatchSnapshot();
          case 4:
          case "end":
            return _context6.stop();
        }
      }
    }, _callee6);
  })));
  it('can work with unescaped JSON pointers with ~0', /*#__PURE__*/(0, _asyncToGenerator2["default"])( /*#__PURE__*/_regenerator["default"].mark(function _callee7() {
    var jsonAst;
    return _regenerator["default"].wrap(function _callee7$(_context7) {
      while (1) {
        switch (_context7.prev = _context7.next) {
          case 0:
            _context7.next = 2;
            return loadScenario(5);
          case 2:
            jsonAst = _context7.sent;
            expect((0, _.getMetaFromPath)(jsonAst, '/foo/~0some~0path/value')).toMatchSnapshot();
          case 4:
          case "end":
            return _context7.stop();
        }
      }
    }, _callee7);
  })));
});