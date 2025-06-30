const Options = require('./options');

/**
 * Normalizes the given arguments, accounting for optional args.
 *
 * @param {Arguments} args
 * @returns {object}
 */
module.exports = function normalizeArgs(args) {
  let path;
  let schema;
  let options;
  let callback;

  // eslint-disable-next-line no-param-reassign
  args = Array.prototype.slice.call(args);

  if (typeof args[args.length - 1] === 'function') {
    // The last parameter is a callback function
    callback = args.pop();
  }

  if (typeof args[0] === 'string') {
    // The first parameter is the path
    path = args[0];
    if (typeof args[2] === 'object') {
      // The second parameter is the schema, and the third parameter is the options
      schema = args[1];
      options = args[2];
    } else {
      // The second parameter is the options
      schema = undefined;
      options = args[1];
    }
  } else {
    // The first parameter is the schema
    path = '';
    schema = args[0];
    options = args[1];
  }

  if (!(options instanceof Options)) {
    options = new Options(options);
  }

  return {
    path,
    schema,
    options,
    callback,
  };
};
