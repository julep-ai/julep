import { source } from '@/lib/source';
import { createFromSource } from 'fumadocs-core/search/server';

// Static export: emit a statically cached JSON index for search.
// https://fumadocs.dev/docs/headless/search/orama#static-export
export const revalidate = false;
export const { staticGET: GET } = createFromSource(source, {
  language: 'english',
});
