export function patchCreate(client: any, scope: any = null) {
  if (!scope) {
    scope = client;
  }

  const originalCreate = client.create.bind(client);
  client.create = (settings: { [key: string]: any }) => {
    settings.model = settings.model || "julep-ai/samantha-1-turbo";

    return originalCreate.call(scope, settings);
  };

  return client;
}
