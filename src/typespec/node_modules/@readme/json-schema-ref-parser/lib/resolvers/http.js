const http = require('http');
const https = require('https');

const { ono } = require('@jsdevtools/ono');

const { ResolverError } = require('../util/errors');
const url = require('../util/url');

/**
 * Sends an HTTP GET request.
 *
 * @param {Url} u - A parsed {@link Url} object
 * @param {object} httpOptions - The `options.resolve.http` object
 *
 * @returns {Promise<Response>}
 * The promise resolves with the HTTP Response object.
 */
function get(u, httpOptions) {
  return new Promise((resolve, reject) => {
    // console.log('GET', u.href);

    const protocol = u.protocol === 'https:' ? https : http;
    const req = protocol.get({
      hostname: u.hostname,
      port: u.port,
      path: u.path,
      auth: u.auth,
      protocol: u.protocol,
      headers: httpOptions.headers || {},
      withCredentials: httpOptions.withCredentials,
    });

    if (typeof req.setTimeout === 'function') {
      req.setTimeout(httpOptions.timeout);
    }

    req.on('timeout', () => {
      req.abort();
    });

    req.on('error', reject);

    req.once('response', res => {
      res.body = Buffer.alloc(0);

      res.on('data', data => {
        res.body = Buffer.concat([res.body, Buffer.from(data)]);
      });

      res.on('error', reject);

      res.on('end', () => {
        resolve(res);
      });
    });
  });
}

/**
 * Downloads the given file.
 *
 * @param {Url|string} u        - The url to download (can be a parsed {@link Url} object)
 * @param {object} httpOptions  - The `options.resolve.http` object
 * @param {number} [redirects]  - The redirect URLs that have already been followed
 *
 * @returns {Promise<Buffer>}
 * The promise resolves with the raw downloaded data, or rejects if there is an HTTP error.
 */
function download(u, httpOptions, redirects) {
  return new Promise((resolve, reject) => {
    u = url.parse(u); // eslint-disable-line no-param-reassign
    redirects = redirects || []; // eslint-disable-line no-param-reassign
    redirects.push(u.href);

    get(u, httpOptions)
      .then(res => {
        if (res.statusCode >= 400) {
          throw ono({ status: res.statusCode }, `HTTP ERROR ${res.statusCode}`);
        } else if (res.statusCode >= 300) {
          if (redirects.length > httpOptions.redirects) {
            reject(
              new ResolverError(
                ono(
                  { status: res.statusCode },
                  `Error downloading ${redirects[0]}. \nToo many redirects: \n  ${redirects.join(' \n  ')}`
                )
              )
            );
          } else if (!res.headers.location) {
            throw ono({ status: res.statusCode }, `HTTP ${res.statusCode} redirect with no location header`);
          } else {
            // console.log('HTTP %d redirect %s -> %s', res.statusCode, u.href, res.headers.location);
            const redirectTo = url.resolve(u, res.headers.location);
            download(redirectTo, httpOptions, redirects).then(resolve, reject);
          }
        } else {
          resolve(res.body || Buffer.alloc(0));
        }
      })
      .catch(err => {
        reject(new ResolverError(ono(err, `Error downloading ${u.href}`), u.href));
      });
  });
}

module.exports = {
  /**
   * The order that this resolver will run, in relation to other resolvers.
   *
   * @type {number}
   */
  order: 200,

  /**
   * HTTP headers to send when downloading files.
   *
   * @example:
   * {
   *   "User-Agent": "JSON Schema $Ref Parser",
   *   Accept: "application/json"
   * }
   *
   * @type {object}
   */
  headers: null,

  /**
   * HTTP request timeout (in milliseconds).
   *
   * @type {number}
   */
  timeout: 5000, // 5 seconds

  /**
   * The maximum number of HTTP redirects to follow.
   * To disable automatic following of redirects, set this to zero.
   *
   * @type {number}
   */
  redirects: 5,

  /**
   * The `withCredentials` option of XMLHttpRequest.
   * Set this to `true` if you're downloading files from a CORS-enabled server that requires authentication
   *
   * @type {boolean}
   */
  withCredentials: false,

  /**
   * Determines whether this resolver can read a given file reference.
   * Resolvers that return true will be tried in order, until one successfully resolves the file.
   * Resolvers that return false will not be given a chance to resolve the file.
   *
   * @param {object} file           - An object containing information about the referenced file
   * @param {string} file.url       - The full URL of the referenced file
   * @param {string} file.extension - The lowercased file extension (e.g. ".txt", ".html", etc.)
   * @returns {boolean}
   */
  canRead(file) {
    return url.isHttp(file.url);
  },

  /**
   * Reads the given URL and returns its raw contents as a Buffer.
   *
   * @param {object} file           - An object containing information about the referenced file
   * @param {string} file.url       - The full URL of the referenced file
   * @param {string} file.extension - The lowercased file extension (e.g. ".txt", ".html", etc.)
   * @returns {Promise<Buffer>}
   */
  read(file) {
    const u = url.parse(file.url);

    if (process.browser && !u.protocol) {
      // Use the protocol of the current page
      // eslint-disable-next-line no-restricted-globals
      u.protocol = url.parse(location.href).protocol;
    }

    return download(u, this);
  },
};
