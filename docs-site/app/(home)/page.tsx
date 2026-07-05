import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex flex-col justify-center text-center flex-1 px-6">
      <h1 className="text-4xl font-bold mb-4">Julep</h1>
      <p className="text-fd-muted-foreground max-w-2xl mx-auto">
        Durable AI agents — flows that crash and resume, retry safely,
        explain every step through a derived projection, and deny any tool the model was not
        granted. Author with <code>@flow</code>; ship the same frozen IR to Temporal, Kubernetes,
        or DBOS.
      </p>
      <div className="mt-8 flex items-center justify-center gap-4">
        <Link href="/docs" className="font-medium underline">
          Read the docs
        </Link>
        <Link href="/docs/start/install" className="font-medium underline">
          Get started
        </Link>
        <a
          className="font-medium underline"
          href="https://github.com/julep-ai/julep-v2"
          rel="noreferrer noopener"
          target="_blank"
        >
          GitHub
        </a>
      </div>
    </div>
  );
}
