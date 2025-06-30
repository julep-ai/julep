import { OpenAPI } from 'openapi-types';

export = OpenAPIParser;

/**
 * This is the default export of Swagger Parser. You can creates instances of this class using new OpenAPIParser(), or you can just call its static methods.
 *
 * See https://apitools.dev/swagger-parser/docs/swagger-parser.html
 */
declare class OpenAPIParser {
  /**
   * The `api` property is the parsed/bundled/dereferenced OpenAPI definition. This is the same value that is passed to the callback function (or Promise) when calling the parse, bundle, or dereference methods.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#api
   */
  public api: OpenAPI.Document;

  /**
   * The $refs property is a `$Refs` object, which lets you access all of the externally-referenced files in the OpenAPI definition, as well as easily get and set specific values in the OpenAPI definition using JSON pointers.
   *
   * This is the same value that is passed to the callback function (or Promise) when calling the `resolve` method.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#refs
   */
  public $refs: OpenAPIParser.$Refs;

  /**
   * Parses, dereferences, and validates the given Swagger API.
   * Depending on the options, validation can include JSON Schema validation and/or Swagger Spec validation.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#validateapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. See the `parse` method for more info.
   * @param options (optional)
   * @param callback (optional) A callback that will receive the dereferenced OpenAPI definition
   */
  public validate(api: string | OpenAPI.Document, callback: OpenAPIParser.ApiCallback): void;
  public validate(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public validate(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public validate(api: string | OpenAPI.Document): Promise<OpenAPI.Document>;
  public validate(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPI.Document>;
  public validate(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPI.Document>;

  /**
   * Parses, dereferences, and validates the given Swagger API.
   * Depending on the options, validation can include JSON Schema validation and/or Swagger Spec validation.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#validateapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. See the `parse` method for more info.
   * @param options (optional)
   * @param callback (optional) A callback that will receive the dereferenced OpenAPI definition
   */
  public static validate(api: string | OpenAPI.Document, callback: OpenAPIParser.ApiCallback): void;
  public static validate(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public static validate(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public static validate(api: string | OpenAPI.Document): Promise<OpenAPI.Document>;
  public static validate(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPI.Document>;
  public static validate(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPI.Document>;

  /**
   * Dereferences all `$ref` pointers in the OpenAPI definition, replacing each reference with its resolved value. This results in an API definition that does not contain any `$ref` pointers. Instead, it's a normal JavaScript object tree that can easily be crawled and used just like any other JavaScript object. This is great for programmatic usage, especially when using tools that don't understand JSON references.
   *
   * The dereference method maintains object reference equality, meaning that all `$ref` pointers that point to the same object will be replaced with references to the same object. Again, this is great for programmatic usage, but it does introduce the risk of circular references, so be careful if you intend to serialize the API definition using `JSON.stringify()`. Consider using the bundle method instead, which does not create circular references.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#dereferenceapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. See the `parse` method for more info.
   * @param options (optional)
   * @param callback (optional) A callback that will receive the dereferenced OpenAPI definition
   */
  public dereference(api: string | OpenAPI.Document, callback: OpenAPIParser.ApiCallback): void;
  public dereference(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public dereference(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public dereference(api: string | OpenAPI.Document): Promise<OpenAPI.Document>;
  public dereference(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPI.Document>;
  public dereference(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPI.Document>;

  /**
   * Dereferences all `$ref` pointers in the OpenAPI definition, replacing each reference with its resolved value. This results in an API definition that does not contain any `$ref` pointers. Instead, it's a normal JavaScript object tree that can easily be crawled and used just like any other JavaScript object. This is great for programmatic usage, especially when using tools that don't understand JSON references.
   *
   * The dereference method maintains object reference equality, meaning that all `$ref` pointers that point to the same object will be replaced with references to the same object. Again, this is great for programmatic usage, but it does introduce the risk of circular references, so be careful if you intend to serialize the API definition using `JSON.stringify()`. Consider using the bundle method instead, which does not create circular references.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#dereferenceapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. See the `parse` method for more info.
   * @param options (optional)
   * @param callback (optional) A callback that will receive the dereferenced OpenAPI definition
   */
  public static dereference(api: string | OpenAPI.Document, callback: OpenAPIParser.ApiCallback): void;
  public static dereference(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public static dereference(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public static dereference(api: string | OpenAPI.Document): Promise<OpenAPI.Document>;
  public static dereference(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPI.Document>;
  public static dereference(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPI.Document>;

  /**
   * Bundles all referenced files/URLs into a single API definition that only has internal `$ref` pointers. This lets you split-up your API definition however you want while you're building it, but easily combine all those files together when it's time to package or distribute the API definition to other people. The resulting API definition size will be small, since it will still contain internal JSON references rather than being fully-dereferenced.
   *
   * This also eliminates the risk of circular references, so the API definition can be safely serialized using `JSON.stringify()`.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#bundleapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. See the `parse` method for more info.
   * @param options (optional)
   * @param callback (optional) A callback that will receive the bundled API definition object
   */
  public bundle(api: string | OpenAPI.Document, callback: OpenAPIParser.ApiCallback): void;
  public bundle(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public bundle(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public bundle(api: string | OpenAPI.Document): Promise<OpenAPI.Document>;
  public bundle(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPI.Document>;
  public bundle(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPI.Document>;

  /**
   * Bundles all referenced files/URLs into a single API definition that only has internal `$ref` pointers. This lets you split-up your API definition however you want while you're building it, but easily combine all those files together when it's time to package or distribute the API definition to other people. The resulting API definition size will be small, since it will still contain internal JSON references rather than being fully-dereferenced.
   *
   * This also eliminates the risk of circular references, so the API definition can be safely serialized using `JSON.stringify()`.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#bundleapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. See the `parse` method for more info.
   * @param options (optional)
   * @param callback (optional) A callback that will receive the bundled API definition object
   */
  public static bundle(api: string | OpenAPI.Document, callback: OpenAPIParser.ApiCallback): void;
  public static bundle(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public static bundle(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public static bundle(api: string | OpenAPI.Document): Promise<OpenAPI.Document>;
  public static bundle(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPI.Document>;
  public static bundle(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPI.Document>;

  /**
   * *This method is used internally by other methods, such as `bundle` and `dereference`. You probably won't need to call this method yourself.*
   *
   * Parses the given OpenAPI definition file (in JSON or YAML format), and returns it as a JavaScript object. This method `does not` resolve `$ref` pointers or dereference anything. It simply parses one file and returns it.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#parseapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. The path can be absolute or relative. In Node, the path is relative to `process.cwd()`. In the browser, it's relative to the URL of the page.
   * @param options (optional)
   * @param callback (optional) A callback that will receive the parsed OpenAPI definition object, or an error
   */
  public parse(api: string | OpenAPI.Document, callback: OpenAPIParser.ApiCallback): void;
  public parse(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public parse(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public parse(api: string | OpenAPI.Document): Promise<OpenAPI.Document>;
  public parse(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPI.Document>;
  public parse(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPI.Document>;

  /**
   * *This method is used internally by other methods, such as `bundle` and `dereference`. You probably won't need to call this method yourself.*
   *
   * Parses the given OpenAPI definition file (in JSON or YAML format), and returns it as a JavaScript object. This method `does not` resolve `$ref` pointers or dereference anything. It simply parses one file and returns it.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#parseapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. The path can be absolute or relative. In Node, the path is relative to `process.cwd()`. In the browser, it's relative to the URL of the page.
   * @param options (optional)
   * @param callback (optional) A callback that will receive the parsed OpenAPI definition object, or an error
   */
  public static parse(api: string | OpenAPI.Document, callback: OpenAPIParser.ApiCallback): void;
  public static parse(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public static parse(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.ApiCallback,
  ): void;
  public static parse(api: string | OpenAPI.Document): Promise<OpenAPI.Document>;
  public static parse(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPI.Document>;
  public static parse(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPI.Document>;

  /**
   * *This method is used internally by other methods, such as `bundle` and `dereference`. You probably won't need to call this method yourself.*
   *
   * Resolves all JSON references (`$ref` pointers) in the given OpenAPI definition file. If it references any other files/URLs, then they will be downloaded and resolved as well. This method **does not** dereference anything. It simply gives you a `$Refs` object, which is a map of all the resolved references and their values.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#resolveapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. See the `parse` method for more info.
   * @param options (optional)
   * @param callback (optional) A callback that will receive a `$Refs` object
   */
  public resolve(api: string | OpenAPI.Document, callback: OpenAPIParser.$RefsCallback): void;
  public resolve(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.$RefsCallback,
  ): void;
  public resolve(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.$RefsCallback,
  ): void;
  public resolve(api: string | OpenAPI.Document): Promise<OpenAPIParser.$Refs>;
  public resolve(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPIParser.$Refs>;
  public resolve(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPIParser.$Refs>;

  /**
   * *This method is used internally by other methods, such as `bundle` and `dereference`. You probably won't need to call this method yourself.*
   *
   * Resolves all JSON references (`$ref` pointers) in the given OpenAPI definition file. If it references any other files/URLs, then they will be downloaded and resolved as well. This method **does not** dereference anything. It simply gives you a `$Refs` object, which is a map of all the resolved references and their values.
   *
   * See https://apitools.dev/swagger-parser/docs/swagger-parser.html#resolveapi-options-callback
   *
   * @param api An OpenAPI definition, or the file path or URL of an OpenAPI definition. See the `parse` method for more info.
   * @param options (optional)
   * @param callback (optional) A callback that will receive a `$Refs` object
   */
  public static resolve(api: string | OpenAPI.Document, callback: OpenAPIParser.$RefsCallback): void;
  public static resolve(
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.$RefsCallback,
  ): void;
  public static resolve(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
    callback: OpenAPIParser.$RefsCallback,
  ): void;
  public static resolve(api: string | OpenAPI.Document): Promise<OpenAPIParser.$Refs>;
  public static resolve(api: string | OpenAPI.Document, options: OpenAPIParser.Options): Promise<OpenAPIParser.$Refs>;
  public static resolve(
    baseUrl: string,
    api: string | OpenAPI.Document,
    options: OpenAPIParser.Options,
  ): Promise<OpenAPIParser.$Refs>;
}

// eslint-disable-next-line no-redeclare
declare namespace OpenAPIParser {
  export type ApiCallback = (err: Error | null, api?: OpenAPI.Document) => any;
  export type $RefsCallback = (err: Error | null, $refs?: $Refs) => any;

  /**
   * See https://apitools.dev/swagger-parser/docs/options.html
   */
  export interface Options {
    /**
     * The `parse` options determine how different types of files will be parsed.
     *
     * JSON Schema `$Ref` Parser comes with built-in JSON, YAML, plain-text, and binary parsers, any of which you can configure or disable. You can also add your own custom parsers if you want.
     */
    parse?: {
      json?: ParserOptions | boolean;
      yaml?: ParserOptions | boolean;
      text?: (ParserOptions & { encoding?: string }) | boolean;
      [key: string]: ParserOptions | boolean | undefined;
    };

    /**
     * The `resolve` options control how Swagger Parser will resolve file paths and URLs, and how those files will be read/downloaded.
     *
     * JSON Schema `$Ref` Parser comes with built-in support for HTTP and HTTPS, as well as support for local files (when running in Node.js). You can configure or disable either of these built-in resolvers. You can also add your own custom resolvers if you want.
     */
    resolve?: {
      /**
       * Determines whether external $ref pointers will be resolved. If this option is disabled, then external `$ref` pointers will simply be ignored.
       */
      external?: boolean;
      file?: Partial<ResolverOptions> | boolean;
      http?: HTTPResolverOptions | boolean;
    };

    /**
     * The `dereference` options control how JSON Schema `$Ref` Parser will dereference `$ref` pointers within the JSON schema.
     */
    dereference?: {
      /**
       * Determines whether circular `$ref` pointers are handled.
       *
       * If set to `false`, then a `ReferenceError` will be thrown if the schema contains any circular references.
       *
       * If set to `"ignore"`, then circular references will simply be ignored. No error will be thrown, but the `$Refs.circular` property will still be set to `true`.
       */
      circular?: boolean | 'ignore';
    };

    /**
     * The `validate` options control how Swagger Parser will validate the API.
     */
    validate?: {
      /**
       * If set to `true` then validation errors will be colorized and styled.
       */
      colorizeErrors?: boolean | false;

      /**
       * If set to `false`, then validating against the Swagger 2.0 Schema, OpenAPI 3.0 Schema, or OpenAPI 3.1 Schema is disabled.
       */
      schema?: boolean;

      /**
       * If set to `false`, then validating against the Swagger 2.0 Specification is disabled.
       */
      spec?: boolean;
    };
  }

  export interface HTTPResolverOptions extends Partial<ResolverOptions> {
    /**
     * You can specify any HTTP headers that should be sent when downloading files. For example, some servers may require you to set the `Accept` or `Referrer` header.
     */
    headers?: object;

    /**
     * The amount of time (in milliseconds) to wait for a response from the server when downloading files. The default is 5 seconds.
     */
    timeout?: number;

    /**
     * The maximum number of HTTP redirects to follow per file. The default is 5. To disable automatic following of redirects, set this to zero.
     */
    redirects?: number;

    /**
     * Set this to `true` if you're downloading files from a CORS-enabled server that requires authentication
     */
    withCredentials?: boolean;
  }

  /**
   * JSON Schema `$Ref` Parser comes with built-in resolvers for HTTP and HTTPS URLs, as well as local filesystem paths (when running in Node.js). You can add your own custom resolvers to support additional protocols, or even replace any of the built-in resolvers with your own custom implementation.
   *
   * See https://apitools.dev/json-schema-ref-parser/docs/plugins/resolvers.html
   */
  export interface ResolverOptions {
    /**
     * All resolvers have an order property, even the built-in resolvers. If you don't specify an order property, then your resolver will run last. Specifying `order: 1`, like we did in this example, will make your resolver run first. Or you can squeeze your resolver in-between some of the built-in resolvers. For example, `order: 101` would make it run after the file resolver, but before the HTTP resolver. You can see the order of all the built-in resolvers by looking at their source code.
     *
     * The order property and canRead property are related to each other. For each file that Swagger Parser needs to resolve, it first determines which resolvers can read that file by checking their canRead property. If only one resolver matches a file, then only that one resolver is called, regardless of its order. If multiple resolvers match a file, then those resolvers are tried in order until one of them successfully reads the file. Once a resolver successfully reads the file, the rest of the resolvers are skipped.
     */
    order?: number;

    /**
     * The `canRead` property tells JSON Schema `$Ref` Parser what kind of files your resolver can read. In this example, we've simply specified a regular expression that matches "mogodb://" URLs, but we could have used a simple boolean, or even a function with custom logic to determine which files to resolve. Here are examples of each approach:
     */
    canRead: boolean | RegExp | string | string[] | ((file: FileInfo) => boolean);

    /**
     * This is where the real work of a resolver happens. The `read` method accepts the same file info object as the `canRead` function, but rather than returning a boolean value, the `read` method should return the contents of the file. The file contents should be returned in as raw a form as possible, such as a string or a byte array. Any further parsing or processing should be done by parsers.
     *
     * Unlike the `canRead` function, the `read` method can also be asynchronous. This might be important if your resolver needs to read data from a database or some other external source. You can return your asynchronous value using either an ES6 Promise or a Node.js-style error-first callback. Of course, if your resolver has the ability to return its data synchronously, then that's fine too. Here are examples of all three approaches:
     */
    read(
      file: FileInfo,
      callback?: (error: Error | null, data: string | null) => any,
    ): string | Buffer | Promise<string | Buffer>;
  }

  export interface ParserOptions {
    /**
     * Parsers run in a specific order, relative to other parsers. For example, a parser with `order: 5` will run before a parser with `order: 10`. If a parser is unable to successfully parse a file, then the next parser is tried, until one succeeds or they all fail.
     *
     * You can change the order in which parsers run, which is useful if you know that most of your referenced files will be a certain type, or if you add your own custom parser that you want to run first.
     */
    order?: number;

    /**
     * All of the built-in parsers allow empty files by default. The JSON and YAML parsers will parse empty files as `undefined`. The text parser will parse empty files as an empty string. The binary parser will parse empty files as an empty byte array.
     *
     * You can set `allowEmpty: false` on any parser, which will cause an error to be thrown if a file empty.
     */
    allowEmpty?: boolean;

    /**
     * Determines which parsers will be used for which files.
     *
     * A regular expression can be used to match files by their full path. A string (or array of strings) can be used to match files by their file extension. Or a function can be used to perform more complex matching logic. See the custom parser docs for details.
     */
    canParse?: boolean | RegExp | string | string[] | ((file: FileInfo) => boolean);
  }

  /**
   * JSON Schema `$Ref` Parser supports plug-ins, such as resolvers and parsers. These plug-ins can have methods such as `canRead()`, `read()`, `canParse()`, and `parse()`. All of these methods accept the same object as their parameter: an object containing information about the file being read or parsed.
   *
   * The file info object currently only consists of a few properties, but it may grow in the future if plug-ins end up needing more information.
   *
   * See https://apitools.dev/json-schema-ref-parser/docs/plugins/file-info-object.html
   */
  export interface FileInfo {
    /**
     * The full URL of the file. This could be any type of URL, including "http://", "https://", "file://", "ftp://", "mongodb://", or even a local filesystem path (when running in Node.js).
     */
    url: string;

    /**
     * The lowercase file extension, such as ".json", ".yaml", ".txt", etc.
     */
    extension: string;

    /**
     * The raw file contents, in whatever form they were returned by the resolver that read the file.
     */
    data: string | Buffer;
  }

  /**
   * When you call the resolve method, the value that gets passed to the callback function (or Promise) is a $Refs object. This same object is accessible via the parser.$refs property of OpenAPIParser objects.
   *
   * This object is a map of JSON References and their resolved values. It also has several convenient helper methods that make it easy for you to navigate and manipulate the JSON References.
   *
   * See https://apitools.dev/swagger-parser/docs/refs.html
   */
  export class $Refs {
    /**
     * This property is true if the API definition contains any circular references. You may want to check this property before serializing the dereferenced API definition as JSON, since JSON.stringify() does not support circular references by default.
     *
     * See https://apitools.dev/swagger-parser/docs/refs.html#circular
     */
    public circular: boolean;

    /**
     * Returns the paths/URLs of all the files in your API definition (including the main API definition file).
     *
     * See https://apitools.dev/swagger-parser/docs/refs.html#pathstypes
     *
     * @param types (optional) Optionally only return certain types of paths ("file", "http", etc.)
     */
    public paths(...types: string[]): string[];

    /**
     * Returns a map of paths/URLs and their correspond values.
     *
     * See https://apitools.dev/swagger-parser/docs/refs.html#valuestypes
     *
     * @param types (optional) Optionally only return values from certain locations ("file", "http", etc.)
     */
    public values(...types: string[]): { [url: string]: any };

    /**
     * Returns `true` if the given path exists in the OpenAPI definition; otherwise, returns `false`
     *
     * See https://apitools.dev/swagger-parser/docs/refs.html#existsref
     *
     * @param $ref The JSON Reference path, optionally with a JSON Pointer in the hash
     */
    public exists($ref: string): boolean;

    /**
     * Gets the value at the given path in the OpenAPI definition. Throws an error if the path does not exist.
     *
     * See https://apitools.dev/swagger-parser/docs/refs.html#getref
     *
     * @param $ref The JSON Reference path, optionally with a JSON Pointer in the hash
     */
    public get($ref: string): any;

    /**
     * Sets the value at the given path in the OpenAPI definition. If the property, or any of its parents, don't exist, they will be created.
     *
     * @param $ref The JSON Reference path, optionally with a JSON Pointer in the hash
     * @param value The value to assign. Can be anything (object, string, number, etc.)
     */
    public set($ref: string, value: any): void;
  }
}
