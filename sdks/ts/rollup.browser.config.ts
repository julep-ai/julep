import typescript from "rollup-plugin-typescript2";
import pkg from "./package.json";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import json from "@rollup/plugin-json";
import strip from "@rollup/plugin-strip";
import { optimizeLodashImports } from "@optimize-lodash/rollup-plugin";

export default {
  input: "src/index.ts",
  output: [
    {
      dir: pkg.browser.replace("index.js", ""),
      format: "cjs",
      sourcemap: true,
      strict: false,
    },
  ],
  plugins: [
    typescript({
      rollupCommonJSResolveHack: false,
      clean: true,
      tsconfig: "./tsconfig.json",
    }),
    commonjs({
      transformMixedEsModules: true,
      requireReturnsDefault: "auto",
    }),
    nodeResolve({
      exportConditions: ["browser"],
      browser: true,
    }),
    optimizeLodashImports(),
    strip(),
    json(),
  ],
};
