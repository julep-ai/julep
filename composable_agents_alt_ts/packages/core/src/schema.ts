import type { JSONSchema, Node, ToolManifest } from './types.js';
import { getStepToolHash } from './util.js';

export function schemaSummary(schema: JSONSchema | undefined): string {
  if (!schema || Object.keys(schema).length === 0) return 'unknown';
  const t = schemaType(schema)?.join('|') ?? 'any';
  const req = requiredProps(schema);
  return req.length ? `${t}{${req.join(',')}}` : t;
}

export function schemasCompatible(output: JSONSchema | undefined, input: JSONSchema | undefined): boolean {
  return isSchemaAssignable(output, input);
}

// Conservative, partial JSON Schema assignability. Unknown schemas are accepted to preserve velocity;
// teams can layer full JSON Schema validation in adapters or stricter deploy policies.
export function isSchemaAssignable(output?: JSONSchema, input?: JSONSchema): boolean {
  if (!output || !input) return true;
  if (isEmpty(output) || isEmpty(input)) return true;
  if (input.anyOf || input.oneOf || input.allOf || output.anyOf || output.oneOf || output.allOf) return true;

  const outT = schemaType(output);
  const inT = schemaType(input);
  if (outT && inT && !outT.some((t) => inT.includes(t))) return false;

  if (outT?.includes('object') || inT?.includes('object')) {
    const outProps = objectProps(output);
    const inProps = objectProps(input);
    const outReq = new Set(requiredProps(output));
    for (const req of requiredProps(input)) {
      if (!outProps[req]) return false;
      if (!outReq.has(req)) return false;
      if (!isSchemaAssignable(outProps[req], inProps[req])) return false;
    }
  }

  if (outT?.includes('array') || inT?.includes('array')) {
    const outItems = firstArrayItemSchema(output);
    const inItems = firstArrayItemSchema(input);
    if (outItems && inItems && !isSchemaAssignable(outItems, inItems)) return false;
  }

  return true;
}

export function inferInputSchema(n: Node, manifest?: ToolManifest): JSONSchema | undefined {
  if (n.inputSchema) return n.inputSchema;
  if (n.ann?.inputSchema) return n.ann.inputSchema;
  switch (n.op) {
    case 'ident':
    case 'arr':
      return n.ann?.inputSchema;
    case 'prim':
      return inputSchemaForStep(n, manifest);
    case 'seq':
      return n.left ? inferInputSchema(n.left, manifest) : undefined;
    case 'par':
    case 'alt':
      return mergeInputSchemas(inferInputSchema(n.left!, manifest), inferInputSchema(n.right!, manifest));
    case 'iter_up_to':
      return n.body ? inferInputSchema(n.body, manifest) : undefined;
    case 'eval_plan':
      return n.plan ? inferInputSchema(n.plan, manifest) : n.ann?.inputSchema;
    case 'app':
      return n.ann?.inputSchema;
  }
}

export function inferOutputSchema(n: Node, manifest?: ToolManifest): JSONSchema | undefined {
  if (n.outputSchema) return n.outputSchema;
  if (n.ann?.outputSchema) return n.ann.outputSchema;
  switch (n.op) {
    case 'ident':
      return n.ann?.inputSchema ?? n.ann?.outputSchema;
    case 'arr':
      return n.ann?.outputSchema;
    case 'prim':
      return outputSchemaForStep(n, manifest);
    case 'seq':
      return n.right ? inferOutputSchema(n.right, manifest) : undefined;
    case 'par': {
      const left = inferOutputSchema(n.left!, manifest);
      const right = inferOutputSchema(n.right!, manifest);
      return { type: 'array', prefixItems: [left ?? {}, right ?? {}], minItems: 2, maxItems: 2 };
    }
    case 'alt': {
      const left = inferOutputSchema(n.left!, manifest);
      const right = inferOutputSchema(n.right!, manifest);
      if (!left) return right;
      if (!right) return left;
      return { anyOf: [left, right] };
    }
    case 'iter_up_to':
      return n.body ? inferOutputSchema(n.body, manifest) : undefined;
    case 'eval_plan':
      return n.plan ? inferOutputSchema(n.plan, manifest) : n.ann?.outputSchema;
    case 'app':
      return n.ann?.outputSchema;
  }
}

function inputSchemaForStep(n: Node, manifest?: ToolManifest): JSONSchema | undefined {
  const step = n.step;
  if (!step) return undefined;
  if ('inputSchema' in step && step.inputSchema) return step.inputSchema;
  if (step.kind === 'think') return step.promptSchema;
  if (step.kind === 'sub') return step.contract.inputSchema;
  if (step.kind === 'call') return manifest?.[getStepToolHash(step) ?? '']?.inputSchema;
  return undefined;
}

function outputSchemaForStep(n: Node, manifest?: ToolManifest): JSONSchema | undefined {
  const step = n.step;
  if (!step) return undefined;
  if ('outputSchema' in step && step.outputSchema) return step.outputSchema;
  if (step.kind === 'think') return step.replySchema;
  if (step.kind === 'sub') return step.contract.outputSchema;
  if (step.kind === 'call') return manifest?.[getStepToolHash(step) ?? '']?.outputSchema;
  return undefined;
}

function isEmpty(schema: JSONSchema): boolean {
  return Object.keys(schema).length === 0;
}

function schemaType(schema?: JSONSchema): string[] | undefined {
  const t = schema?.type;
  if (Array.isArray(t)) return t.filter((x): x is string => typeof x === 'string');
  if (typeof t === 'string') return [t];
  return undefined;
}

function objectProps(schema: JSONSchema): Record<string, JSONSchema> {
  const props = schema.properties;
  if (!props || typeof props !== 'object' || Array.isArray(props)) return {};
  return props;
}

function requiredProps(schema: JSONSchema): string[] {
  return Array.isArray(schema.required) ? schema.required.filter((x): x is string => typeof x === 'string') : [];
}

function firstArrayItemSchema(schema: JSONSchema): JSONSchema | undefined {
  const items = schema.items;
  if (Array.isArray(items)) return items[0];
  if (items && typeof items === 'object') return items;
  if (Array.isArray(schema.prefixItems)) return schema.prefixItems[0];
  return undefined;
}

function mergeInputSchemas(a?: JSONSchema, b?: JSONSchema): JSONSchema | undefined {
  if (!a) return b;
  if (!b) return a;
  return { allOf: [a, b] };
}
