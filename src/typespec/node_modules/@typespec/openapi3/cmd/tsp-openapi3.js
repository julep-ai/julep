#!/usr/bin/env node
import { main } from "../dist/src/cli/cli.js";

main().catch((error) => {
  // eslint-disable-next-line no-console
  console.error(error);

  process.exit(1);
});
