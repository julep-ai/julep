#!/usr/bin/env node
import { runScript } from "../dist/src/runner.js";
await runScript("entrypoints/cli.js", "dist/core/cli/cli.js");
