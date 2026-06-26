import { defineConfig, defineDocs, frontmatterSchema, metaSchema } from 'fumadocs-mdx/config';
import { rehypeCodeDefaultOptions } from 'fumadocs-core/mdx-plugins';

// Frontmatter / meta.json schemas: https://fumadocs.dev/docs/mdx/collections
export const docs = defineDocs({
  dir: 'content/docs',
  docs: {
    schema: frontmatterSchema,
  },
  meta: {
    schema: metaSchema,
  },
});

// Render unbundled fence languages (dot, mermaid, haskell, …) as plain text
// instead of throwing a ShikiError. `fallbackLanguage` is honored by
// @shikijs/rehype at runtime; declared as a const so it isn't subject to
// TypeScript's excess-property check on the RehypeCodeOptions type.
const rehypeCodeOptions = { ...rehypeCodeDefaultOptions, fallbackLanguage: 'text' };

export default defineConfig({
  mdxOptions: {
    rehypeCodeOptions,
  },
});
