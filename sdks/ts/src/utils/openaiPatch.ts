/**
 * Patches the 'create' method of an OpenAI client instance to ensure a default model is used if none is specified.
 * This is useful for enforcing a consistent model usage across different parts of the SDK.
 *
 * @param client The OpenAI client instance to be patched.
 * @param scope Optional. The scope in which the original 'create' method is bound. Defaults to the client itself if not provided.
 */
export function patchCreate(client: any, scope: any = null) {
  if (!scope) {
    scope = client;
  }

  const originalCreate = client.create.bind(client);
  client.create = (settings: { [key: string]: any }) => {
    // Set the default model to 'julep-ai/samantha-1-turbo' if none is specified in the settings.
    settings.model = settings.model || "julep-ai/samantha-1-turbo";

    return originalCreate.call(scope, settings);
  };

  return client;
  // After applying this patch, any calls to the 'create' method on the patched client will use the default model unless another model is explicitly specified.
}
