/**
 * Internally, we represent paths as strings with '/' as the directory separator.
 * When we make system calls (eg: LanguageServiceHost.getDirectory()),
 * we expect the host to correctly handle paths in our specified format.
 */
export declare const directorySeparator = "/";
export declare const altDirectorySeparator = "\\";
/**
 * Determines whether a charCode corresponds to `/` or `\`.
 */
export declare function isAnyDirectorySeparator(charCode: number): boolean;
/**
 * Determines whether a path starts with a URL scheme (e.g. starts with `http://`, `ftp://`, `file://`, etc.).
 */
export declare function isUrl(path: string): boolean;
export declare function isPathAbsolute(path: string): boolean;
/**
 * Returns length of the root part of a path or URL (i.e. length of "/", "x:/", "//server/share/, file:///user/files").
 *
 * For example:
 * ```ts
 * getRootLength("a") === 0                   // ""
 * getRootLength("/") === 1                   // "/"
 * getRootLength("c:") === 2                  // "c:"
 * getRootLength("c:d") === 0                 // ""
 * getRootLength("c:/") === 3                 // "c:/"
 * getRootLength("c:\\") === 3                // "c:\\"
 * getRootLength("//server") === 7            // "//server"
 * getRootLength("//server/share") === 8      // "//server/"
 * getRootLength("\\\\server") === 7          // "\\\\server"
 * getRootLength("\\\\server\\share") === 8   // "\\\\server\\"
 * getRootLength("file:///path") === 8        // "file:///"
 * getRootLength("file:///c:") === 10         // "file:///c:"
 * getRootLength("file:///c:d") === 8         // "file:///"
 * getRootLength("file:///c:/path") === 11    // "file:///c:/"
 * getRootLength("file://server") === 13      // "file://server"
 * getRootLength("file://server/path") === 14 // "file://server/"
 * getRootLength("http://server") === 13      // "http://server"
 * getRootLength("http://server/path") === 14 // "http://server/"
 * ```
 */
export declare function getRootLength(path: string): number;
export declare function getDirectoryPath(path: string): string;
/**
 * Returns the path except for its containing directory name.
 * Semantics align with NodeJS's `path.basename` except that we support URL's as well.
 *
 * ```ts
 * // POSIX
 * getBaseFileName("/path/to/file.ext") === "file.ext"
 * getBaseFileName("/path/to/") === "to"
 * getBaseFileName("/") === ""
 * // DOS
 * getBaseFileName("c:/path/to/file.ext") === "file.ext"
 * getBaseFileName("c:/path/to/") === "to"
 * getBaseFileName("c:/") === ""
 * getBaseFileName("c:") === ""
 * // URL
 * getBaseFileName("http://typescriptlang.org/path/to/file.ext") === "file.ext"
 * getBaseFileName("http://typescriptlang.org/path/to/") === "to"
 * getBaseFileName("http://typescriptlang.org/") === ""
 * getBaseFileName("http://typescriptlang.org") === ""
 * getBaseFileName("file://server/path/to/file.ext") === "file.ext"
 * getBaseFileName("file://server/path/to/") === "to"
 * getBaseFileName("file://server/") === ""
 * getBaseFileName("file://server") === ""
 * getBaseFileName("file:///path/to/file.ext") === "file.ext"
 * getBaseFileName("file:///path/to/") === "to"
 * getBaseFileName("file:///") === ""
 * getBaseFileName("file://") === ""
 * ```
 */
export declare function getBaseFileName(path: string): string;
/**
 * Gets the file extension for a path.
 * Normalizes it to lower case.
 *
 * ```ts
 * getAnyExtensionFromPath("/path/to/file.ext") === ".ext"
 * getAnyExtensionFromPath("/path/to/file.ext/") === ".ext"
 * getAnyExtensionFromPath("/path/to/file") === ""
 * getAnyExtensionFromPath("/path/to.ext/file") === ""
 * ```
 */
export declare function getAnyExtensionFromPath(path: string): string;
/**
 * Parse a path into an array containing a root component (at index 0) and zero or more path
 * components (at indices > 0). The result is not normalized.
 * If the path is relative, the root component is `""`.
 * If the path is absolute, the root component includes the first path separator (`/`).
 *
 * ```ts
 * // POSIX
 * getPathComponents("/path/to/file.ext") === ["/", "path", "to", "file.ext"]
 * getPathComponents("/path/to/") === ["/", "path", "to"]
 * getPathComponents("/") === ["/"]
 * // DOS
 * getPathComponents("c:/path/to/file.ext") === ["c:/", "path", "to", "file.ext"]
 * getPathComponents("c:/path/to/") === ["c:/", "path", "to"]
 * getPathComponents("c:/") === ["c:/"]
 * getPathComponents("c:") === ["c:"]
 * // URL
 * getPathComponents("http://typescriptlang.org/path/to/file.ext") === ["http://typescriptlang.org/", "path", "to", "file.ext"]
 * getPathComponents("http://typescriptlang.org/path/to/") === ["http://typescriptlang.org/", "path", "to"]
 * getPathComponents("http://typescriptlang.org/") === ["http://typescriptlang.org/"]
 * getPathComponents("http://typescriptlang.org") === ["http://typescriptlang.org"]
 * getPathComponents("file://server/path/to/file.ext") === ["file://server/", "path", "to", "file.ext"]
 * getPathComponents("file://server/path/to/") === ["file://server/", "path", "to"]
 * getPathComponents("file://server/") === ["file://server/"]
 * getPathComponents("file://server") === ["file://server"]
 * getPathComponents("file:///path/to/file.ext") === ["file:///", "path", "to", "file.ext"]
 * getPathComponents("file:///path/to/") === ["file:///", "path", "to"]
 * getPathComponents("file:///") === ["file:///"]
 * getPathComponents("file://") === ["file://"]
 * ```
 */
export declare function getPathComponents(path: string, currentDirectory?: string): string[];
/**
 * Reduce an array of path components to a more simplified path by navigating any
 * `"."` or `".."` entries in the path.
 */
export declare function reducePathComponents(components: readonly string[]): string[];
/**
 * Combines paths. If a path is absolute, it replaces any previous path. Relative paths are not simplified.
 *
 * ```ts
 * // Non-rooted
 * joinPaths("path", "to", "file.ext") === "path/to/file.ext"
 * joinPaths("path", "dir", "..", "to", "file.ext") === "path/dir/../to/file.ext"
 * // POSIX
 * joinPaths("/path", "to", "file.ext") === "/path/to/file.ext"
 * joinPaths("/path", "/to", "file.ext") === "/to/file.ext"
 * // DOS
 * joinPaths("c:/path", "to", "file.ext") === "c:/path/to/file.ext"
 * joinPaths("c:/path", "c:/to", "file.ext") === "c:/to/file.ext"
 * // URL
 * joinPaths("file:///path", "to", "file.ext") === "file:///path/to/file.ext"
 * joinPaths("file:///path", "file:///to", "file.ext") === "file:///to/file.ext"
 * ```
 */
export declare function joinPaths(path: string, ...paths: (string | undefined)[]): string;
/**
 * Combines and resolves paths. If a path is absolute, it replaces any previous path. Any
 * `.` and `..` path components are resolved. Trailing directory separators are preserved.
 *
 * ```ts
 * resolvePath("/path", "to", "file.ext") === "path/to/file.ext"
 * resolvePath("/path", "to", "file.ext/") === "path/to/file.ext/"
 * resolvePath("/path", "dir", "..", "to", "file.ext") === "path/to/file.ext"
 * ```
 */
export declare function resolvePath(path: string, ...paths: (string | undefined)[]): string;
/**
 * Parse a path into an array containing a root component (at index 0) and zero or more path
 * components (at indices > 0). The result is normalized.
 * If the path is relative, the root component is `""`.
 * If the path is absolute, the root component includes the first path separator (`/`).
 *
 * ```ts
 * getNormalizedPathComponents("to/dir/../file.ext", "/path/") === ["/", "path", "to", "file.ext"]
 * ```
 */
export declare function getNormalizedPathComponents(path: string, currentDirectory: string | undefined): string[];
export declare function getNormalizedAbsolutePath(fileName: string, currentDirectory: string | undefined): string;
export declare function normalizePath(path: string): string;
export declare function getNormalizedAbsolutePathWithoutRoot(fileName: string, currentDirectory: string | undefined): string;
/**
 * Formats a parsed path consisting of a root component (at index 0) and zero or more path
 * segments (at indices > 0).
 *
 * ```ts
 * getPathFromPathComponents(["/", "path", "to", "file.ext"]) === "/path/to/file.ext"
 * ```
 */
export declare function getPathFromPathComponents(pathComponents: readonly string[]): string;
/**
 * Removes a trailing directory separator from a path, if it does not already have one.
 *
 * ```ts
 * removeTrailingDirectorySeparator("/path/to/file.ext") === "/path/to/file.ext"
 * removeTrailingDirectorySeparator("/path/to/file.ext/") === "/path/to/file.ext"
 * ```
 */
export declare function removeTrailingDirectorySeparator(path: string): string;
export declare function ensureTrailingDirectorySeparator(path: string): string;
/**
 * Determines whether a path has a trailing separator (`/` or `\\`).
 */
export declare function hasTrailingDirectorySeparator(path: string): boolean;
/**
 * Normalize path separators, converting `\` into `/`.
 */
export declare function normalizeSlashes(path: string): string;
type GetCanonicalFileName = (fileName: string) => string;
/**
 * Gets a relative path that can be used to traverse between `from` and `to`.
 */
export declare function getRelativePathFromDirectory(from: string, to: string, ignoreCase: boolean): string;
/**
 * Gets a relative path that can be used to traverse between `from` and `to`.
 */
export declare function getRelativePathFromDirectory(fromDirectory: string, to: string, getCanonicalFileName: GetCanonicalFileName): string;
export {};
//# sourceMappingURL=path-utils.d.ts.map