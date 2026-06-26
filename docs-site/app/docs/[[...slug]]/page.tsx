import { source } from '@/lib/source';
import { DocsBody, DocsDescription, DocsPage, DocsTitle } from 'fumadocs-ui/layouts/docs/page';
import { notFound } from 'next/navigation';
import { getMDXComponents } from '@/mdx-components';
import type { Metadata } from 'next';
import { createRelativeLink } from 'fumadocs-ui/mdx';

export default async function Page(props: PageProps<'/docs/[[...slug]]'>) {
  const params = await props.params;
  const page = source.getPage(params.slug);
  if (!page) notFound();

  const MDX = page.data.body;
  // Override the repo/branch with NEXT_PUBLIC_GITHUB_REPO / NEXT_PUBLIC_GITHUB_BRANCH if needed.
  const githubRepo = process.env.NEXT_PUBLIC_GITHUB_REPO ?? 'https://github.com/julep-ai/julep-v2';
  const githubBranch = process.env.NEXT_PUBLIC_GITHUB_BRANCH ?? 'main';
  const githubUrl = `${githubRepo.replace(/\/+$/, '')}/blob/${githubBranch}/docs-site/content/docs/${page.path}`;

  return (
    <DocsPage toc={page.data.toc} full={page.data.full}>
      <DocsTitle>{page.data.title}</DocsTitle>
      <DocsDescription className="mb-0">{page.data.description}</DocsDescription>
      <div className="flex flex-row gap-2 items-center border-b pb-6">
        <a
          className="text-sm underline"
          href={githubUrl}
          rel="noreferrer noopener"
          target="_blank"
        >
          Edit on GitHub
        </a>
      </div>
      <DocsBody>
        <MDX
          components={getMDXComponents({
            // allows linking to other pages with relative file paths
            a: createRelativeLink(source, page),
          })}
        />
      </DocsBody>
    </DocsPage>
  );
}

export async function generateStaticParams() {
  return source.generateParams();
}

export async function generateMetadata(props: PageProps<'/docs/[[...slug]]'>): Promise<Metadata> {
  const params = await props.params;
  const page = source.getPage(params.slug);
  if (!page) notFound();

  return {
    title: page.data.title,
    description: page.data.description,
  };
}
