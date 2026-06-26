import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const config = {
  reactStrictMode: true,
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },

  // GitHub Pages (project pages) needs a base path like "/julep-v2".
  // Set NEXT_PUBLIC_BASE_PATH in the deploy workflow if hosting under a subpath.
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH || '',
};

export default withMDX(config);
