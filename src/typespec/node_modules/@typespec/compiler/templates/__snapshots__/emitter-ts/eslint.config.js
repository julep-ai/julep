// @ts-check
import eslint from "@eslint/js";
import tsEslint from "typescript-eslint";

export default tsEslint.config(
  {
    ignores: ["**/dist/**/*", "**/.temp/**/*"],
  },
  eslint.configs.recommended,
  ...tsEslint.configs.recommended,
);
