import { mkdtemp, readdir, rm } from "fs/promises";
import os from "os";
import { compilerAssert } from "../diagnostics.js";
import { joinPaths } from "../path-utils.js";
import { run } from "./utils.js";
export async function installVsix(host, pkg, install) {
    // download npm package to temporary directory
    const temp = await mkdtemp(joinPaths(os.tmpdir(), "typespec"));
    const npmArgs = ["install"];
    // hide npm output unless --debug was passed to typespec
    if (!host.debug) {
        npmArgs.push("--silent");
    }
    // NOTE: Using cwd=temp with `--prefix .` instead of `--prefix ${temp}` to
    // workaround https://github.com/npm/cli/issues/3256. It's still important
    // to pass --prefix even though we're using cwd as otherwise, npm might
    // find a package.json file in a parent directory and install to that
    // directory.
    npmArgs.push("--prefix", ".");
    // To debug with a locally built package rather than pulling from npm,
    // specify the full path to the packed .tgz using TYPESPEC_DEBUG_VSIX_TGZ
    // environment variable.
    npmArgs.push(process.env.TYPESPEC_DEBUG_VSIX_TGZ ?? pkg);
    run(host, "npm", npmArgs, { cwd: temp });
    // locate .vsix
    const dir = joinPaths(temp, "node_modules", pkg);
    const files = await readdir(dir);
    const vsixPaths = [];
    for (const file of files) {
        if (file.endsWith(".vsix")) {
            vsixPaths.push(joinPaths(dir, file));
        }
    }
    compilerAssert(vsixPaths.length > 0, `Installed ${pkg} from npm, but didn't find any .vsix files in it.`);
    // install extension
    const result = install(vsixPaths);
    // delete temporary directory
    await rm(temp, { recursive: true });
    return result;
}
//# sourceMappingURL=install-vsix.js.map