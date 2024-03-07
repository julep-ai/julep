function patchCreate(client, scope = null) {
  if (!scope) {
    scope = client;
  }

  originalCreate = client.create.bind(client);
  client.create = (settings) => {
    settings.model = settings.model || "julep-ai/samantha-1-turbo";

    return originalCreate.call(scope, settings);
  };

  return client;
}

module.exports = {
  patchCreate,
};
