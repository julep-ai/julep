#!/usr/bin/env node
import { runScript } from "../dist/src/runner.js";
await runScript("entrypoints/server.js", "dist/server/server.js");
