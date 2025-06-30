const parse = require('./parse');
const Pointer = require('./pointer');
const $Ref = require('./ref');
const { isHandledError } = require('./util/errors');
const url = require('./util/url');

module.exports = resolveExternal;

/**
 * Crawls the JSON schema, finds all external JSON references, and resolves their values.
 * This method does not mutate the JSON schema. The resolved values are added to {@link $RefParser#$refs}.
 *
 * NOTE: We only care about EXTERNAL references here. INTERNAL references are only relevant when dereferencing.
 *
 * @param {$RefParser} parser
 * @param {$RefParserOptions} options
 *
 * @returns {Promise}
 * The promise resolves once all JSON references in the schema have been resolved,
 * including nested references that are contained in externally-referenced files.
 */
function resolveExternal(parser, options) {
  if (!options.resolve.external) {
    // Nothing to resolve, so exit early
    return Promise.resolve();
  }

  try {
    // console.log('Resolving $ref pointers in %s', parser.$refs._root$Ref.path);
    const promises = crawl(parser.schema, `${parser.$refs._root$Ref.path}#`, parser.$refs, options);
    return Promise.all(promises);
  } catch (e) {
    return Promise.reject(e);
  }
}

/**
 * Recursively crawls the given value, and resolves any external JSON references.
 *
 * @param {*} obj - The value to crawl. If it's not an object or array, it will be ignored.
 * @param {string} path - The full path of `obj`, possibly with a JSON Pointer in the hash
 * @param {$Refs} $refs
 * @param {$RefParserOptions} options
 * @param {Set} seen - Internal.
 *
 * @returns {Promise[]}
 * Returns an array of promises. There will be one promise for each JSON reference in `obj`.
 * If `obj` does not contain any JSON references, then the array will be empty.
 * If any of the JSON references point to files that contain additional JSON references,
 * then the corresponding promise will internally reference an array of promises.
 */
function crawl(obj, path, $refs, options, seen) {
  // eslint-disable-next-line no-param-reassign
  seen = seen || new Set();
  let promises = [];

  if (obj && typeof obj === 'object' && !ArrayBuffer.isView(obj) && !seen.has(obj)) {
    seen.add(obj); // Track previously seen objects to avoid infinite recursion
    if ($Ref.isExternal$Ref(obj)) {
      promises.push(resolve$Ref(obj, path, $refs, options));
    } else {
      for (const key of Object.keys(obj)) {
        const keyPath = Pointer.join(path, key);
        const value = obj[key];

        if ($Ref.isExternal$Ref(value)) {
          promises.push(resolve$Ref(value, keyPath, $refs, options));
        } else {
          promises = promises.concat(crawl(value, keyPath, $refs, options, seen));
        }
      }
    }
  }

  return promises;
}

/**
 * Resolves the given JSON Reference, and then crawls the resulting value.
 *
 * @param {{$ref: string}} $ref - The JSON Reference to resolve
 * @param {string} path - The full path of `$ref`, possibly with a JSON Pointer in the hash
 * @param {$Refs} $refs
 * @param {$RefParserOptions} options
 *
 * @returns {Promise}
 * The promise resolves once all JSON references in the object have been resolved,
 * including nested references that are contained in externally-referenced files.
 */
async function resolve$Ref($ref, path, $refs, options) {
  // console.log('Resolving $ref pointer "%s" at %s', $ref.$ref, path);

  const resolvedPath = url.resolve(path, $ref.$ref);
  const withoutHash = url.stripHash(resolvedPath);

  // Do we already have this $ref?
  // eslint-disable-next-line no-param-reassign
  $ref = $refs._$refs[withoutHash];
  if ($ref) {
    // We've already parsed this $ref, so use the existing value
    return Promise.resolve($ref.value);
  }

  // Parse the $referenced file/url
  try {
    const result = await parse(resolvedPath, $refs, options);

    // Crawl the parsed value
    // console.log('Resolving $ref pointers in %s', withoutHash);
    const promises = crawl(result, `${withoutHash}#`, $refs, options);

    return Promise.all(promises);
  } catch (err) {
    if (!options.continueOnError || !isHandledError(err)) {
      throw err;
    }

    if ($refs._$refs[withoutHash]) {
      err.source = url.stripHash(path);
      err.path = url.safePointerToPath(url.getHash(path));
    }

    return [];
  }
}
