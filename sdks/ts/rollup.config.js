const typescript = require("rollup-plugin-typescript2");
const pkg = require("./package.json");
const { nodeResolve } = require("@rollup/plugin-node-resolve");
const commonjs = require("@rollup/plugin-commonjs");
const json = require("@rollup/plugin-json");
const strip = require("@rollup/plugin-strip");
const { optimizeLodashImports } = require("@optimize-lodash/rollup-plugin");

module.exports = {
  input: "src/index.ts",
  output: [
    {
      dir: pkg.main.replace("/index.js", ""),
      format: "cjs",
      exports: "named",
      sourcemap: true,
      strict: false,
    },
    {
      dir: pkg.module.replace("/index.js", ""),
      format: "es",
      exports: "named",
      sourcemap: true,
      strict: false,
    },
  ],
  plugins: [
    typescript(),
    nodeResolve({ exportConditions: ["node"], inlineDynamicImports: true }),
    commonjs(),
    optimizeLodashImports(),
    strip(),
    json(),
  ],
};
