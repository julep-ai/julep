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
      dir: pkg.main.replace("index.js", ""),
      format: "cjs",
      exports: "named",
      sourcemap: true,
      strict: false,
      plugins: [],
    },
    {
      dir: pkg.module.replace("index.js", ""),
      format: "es",
      sourcemap: true,
    },
  ],
  plugins: [
    typescript({
      rollupCommonJSResolveHack: false,
      clean: true,
      tsconfig: "./tsconfig.json",
    }),
    nodeResolve({ exportConditions: ["node"], browser: true }),
    commonjs({ ignoreGlobal: true }),
    optimizeLodashImports(),
    strip(),
    json(),
  ],
};
