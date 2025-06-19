import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { ClientCapabilities } from './types.js';

// AIDEV-NOTE: Schema transformers adapted from SDK MCP server with additional client support

export type JSONSchema = {
  type?: string;
  properties?: Record<string, JSONSchema>;
  required?: string[];
  anyOf?: JSONSchema[];
  $ref?: string;
  $defs?: Record<string, JSONSchema>;
  [key: string]: any;
};

interface ToolWithHandler {
  tool: Tool;
  handler: any;
  unified: any;
}

export function applyCompatibilityTransformations(
  tools: ToolWithHandler[],
  capabilities: ClientCapabilities
): ToolWithHandler[] {
  let transformedTools = [...tools];

  // Handle top-level unions first as this changes tool names
  if (!capabilities.topLevelUnions) {
    const newTools: ToolWithHandler[] = [];

    for (const toolWithHandler of transformedTools) {
      const variantTools = removeTopLevelUnions(toolWithHandler.tool);

      if (variantTools.length === 1) {
        newTools.push(toolWithHandler);
      } else {
        for (const variantTool of variantTools) {
          newTools.push({
            ...toolWithHandler,
            tool: variantTool,
          });
        }
      }
    }

    transformedTools = newTools;
  }

  // Handle tool name length restrictions
  if (capabilities.toolNameLength) {
    const toolNames = transformedTools.map((t) => t.tool.name);
    const renameMap = truncateToolNames(toolNames, capabilities.toolNameLength);

    transformedTools = transformedTools.map((toolWithHandler) => ({
      ...toolWithHandler,
      tool: {
        ...toolWithHandler.tool,
        name: renameMap.get(toolWithHandler.tool.name) ?? toolWithHandler.tool.name,
      },
    }));
  }

  // Handle schema transformations
  if (!capabilities.refs || !capabilities.unions || !capabilities.formats) {
    transformedTools = transformedTools.map((toolWithHandler) => {
      let schema = toolWithHandler.tool.inputSchema as JSONSchema;

      if (!capabilities.refs) {
        schema = inlineRefs(schema);
      }

      if (!capabilities.unions) {
        schema = removeAnyOf(schema);
      }

      if (!capabilities.formats) {
        schema = removeFormats(schema, capabilities.formats);
      }

      return {
        ...toolWithHandler,
        tool: {
          ...toolWithHandler.tool,
          inputSchema: schema as typeof toolWithHandler.tool.inputSchema,
        },
      };
    });
  }

  return transformedTools;
}

export function truncateToolNames(names: string[], maxLength: number): Map<string, string> {
  if (maxLength <= 0) {
    return new Map();
  }

  const renameMap = new Map<string, string>();
  const usedNames = new Set<string>();

  const toTruncate = names.filter((name) => name.length > maxLength);

  if (toTruncate.length === 0) {
    return renameMap;
  }

  const willCollide =
    new Set(toTruncate.map((name) => name.slice(0, maxLength - 1))).size < toTruncate.length;

  if (!willCollide) {
    for (const name of toTruncate) {
      const truncatedName = name.slice(0, maxLength);
      renameMap.set(name, truncatedName);
    }
  } else {
    const baseLength = maxLength - 1;

    for (const name of toTruncate) {
      const baseName = name.slice(0, baseLength);
      let counter = 1;

      while (usedNames.has(baseName + counter)) {
        counter++;
      }

      const finalName = baseName + counter;
      renameMap.set(name, finalName);
      usedNames.add(finalName);
    }
  }

  return renameMap;
}

export function removeTopLevelUnions(tool: Tool): Tool[] {
  const inputSchema = tool.inputSchema as JSONSchema;
  const variants = inputSchema.anyOf;

  if (!variants || !Array.isArray(variants) || variants.length === 0) {
    return [tool];
  }

  const defs = inputSchema.$defs || {};

  return variants.map((variant, index) => {
    const variantSchema: JSONSchema = {
      ...inputSchema,
      ...variant,
      type: 'object',
      properties: {
        ...(inputSchema.properties || {}),
        ...(variant.properties || {}),
      },
    };

    delete variantSchema.anyOf;

    if (!variantSchema['description']) {
      variantSchema['description'] = tool.description;
    }

    const usedDefs = findUsedDefs(variant, defs);
    if (Object.keys(usedDefs).length > 0) {
      variantSchema.$defs = usedDefs;
    } else {
      delete variantSchema.$defs;
    }

    return {
      ...tool,
      name: `${tool.name}_${toSnakeCase(variant['title'] || `variant${index + 1}`)}`,
      description: variant['description'] || tool.description,
      inputSchema: variantSchema,
    } as Tool;
  });
}

function findUsedDefs(
  schema: JSONSchema,
  defs: Record<string, JSONSchema>,
  visited: Set<string> = new Set()
): Record<string, JSONSchema> {
  const usedDefs: Record<string, JSONSchema> = {};

  if (typeof schema !== 'object' || schema === null) {
    return usedDefs;
  }

  if (schema.$ref) {
    const refParts = schema.$ref.split('/');
    if (refParts[0] === '#' && refParts[1] === '$defs' && refParts[2]) {
      const defName = refParts[2];
      const def = defs[defName];
      if (def && !visited.has(schema.$ref)) {
        usedDefs[defName] = def;
        visited.add(schema.$ref);
        Object.assign(usedDefs, findUsedDefs(def, defs, visited));
        visited.delete(schema.$ref);
      }
    }
    return usedDefs;
  }

  for (const key in schema) {
    if (key !== '$defs' && typeof schema[key] === 'object' && schema[key] !== null) {
      Object.assign(usedDefs, findUsedDefs(schema[key] as JSONSchema, defs, visited));
    }
  }

  return usedDefs;
}

export function inlineRefs(schema: JSONSchema): JSONSchema {
  if (!schema || typeof schema !== 'object') {
    return schema;
  }

  const clonedSchema = { ...schema };
  const defs: Record<string, JSONSchema> = schema.$defs || {};

  delete clonedSchema.$defs;

  const result = inlineRefsRecursive(clonedSchema, defs, new Set<string>());
  return result === null ? {} : result;
}

function inlineRefsRecursive(
  schema: JSONSchema,
  defs: Record<string, JSONSchema>,
  refPath: Set<string>
): JSONSchema | null {
  if (!schema || typeof schema !== 'object') {
    return schema;
  }

  if (Array.isArray(schema)) {
    return schema.map((item) => {
      const processed = inlineRefsRecursive(item, defs, refPath);
      return processed === null ? {} : processed;
    }) as JSONSchema;
  }

  const result = { ...schema };

  if ('$ref' in result && typeof result.$ref === 'string') {
    if (result.$ref.startsWith('#/$defs/')) {
      const refName = result.$ref.split('/').pop() as string;
      const def = defs[refName];

      if (refPath.has(result.$ref)) {
        return null;
      }

      if (def) {
        const newRefPath = new Set(refPath);
        newRefPath.add(result.$ref);

        const inlinedDef = inlineRefsRecursive({ ...def }, defs, newRefPath);

        if (inlinedDef === null) {
          return { ...result };
        }

        const { $ref, ...rest } = result;
        return { ...inlinedDef, ...rest };
      }
    }

    return result;
  }

  for (const key in result) {
    if (result[key] && typeof result[key] === 'object') {
      const processed = inlineRefsRecursive(result[key] as JSONSchema, defs, refPath);
      if (processed === null) {
        delete result[key];
      } else {
        result[key] = processed;
      }
    }
  }

  return result;
}

export function removeAnyOf(schema: JSONSchema): JSONSchema {
  if (!schema || typeof schema !== 'object') {
    return schema;
  }

  if (Array.isArray(schema)) {
    return schema.map((item) => removeAnyOf(item)) as JSONSchema;
  }

  const result = { ...schema };

  if ('anyOf' in result && Array.isArray(result.anyOf) && result.anyOf.length > 0) {
    const firstVariant = result.anyOf[0];

    if (firstVariant && typeof firstVariant === 'object') {
      if (firstVariant.properties && result.properties) {
        result.properties = {
          ...result.properties,
          ...(firstVariant.properties as Record<string, JSONSchema>),
        };
      } else if (firstVariant.properties) {
        result.properties = { ...firstVariant.properties };
      }

      for (const key in firstVariant) {
        if (key !== 'properties') {
          result[key] = firstVariant[key];
        }
      }
    }

    delete result.anyOf;
  }

  for (const key in result) {
    if (result[key] && typeof result[key] === 'object') {
      result[key] = removeAnyOf(result[key] as JSONSchema);
    }
  }

  return result;
}

export function removeFormats(schema: JSONSchema, formatsCapability: boolean): JSONSchema {
  if (formatsCapability) {
    return schema;
  }

  if (!schema || typeof schema !== 'object') {
    return schema;
  }

  if (Array.isArray(schema)) {
    return schema.map((item) => removeFormats(item, formatsCapability)) as JSONSchema;
  }

  const result = { ...schema };

  if ('format' in result && typeof result['format'] === 'string') {
    const formatStr = `(format: "${result['format']}")`;

    if ('description' in result && typeof result['description'] === 'string') {
      result['description'] = `${result['description']} ${formatStr}`;
    } else {
      result['description'] = formatStr;
    }

    delete result['format'];
  }

  for (const key in result) {
    if (result[key] && typeof result[key] === 'object') {
      result[key] = removeFormats(result[key] as JSONSchema, formatsCapability);
    }
  }

  return result;
}

function toSnakeCase(str: string): string {
  return str
    .replace(/\s+/g, '_')
    .replace(/([a-z])([A-Z])/g, '$1_$2')
    .toLowerCase();
}

// Additional helper for parsing embedded JSON (some clients send JSON as strings)
export function parseEmbeddedJSON(args: Record<string, unknown>, schema: Record<string, unknown>) {
  let updated = false;
  const newArgs: Record<string, unknown> = Object.assign({}, args);

  for (const [key, value] of Object.entries(newArgs)) {
    if (typeof value === 'string') {
      try {
        const parsed = JSON.parse(value);
        newArgs[key] = parsed;
        updated = true;
      } catch (e) {
        // Not valid JSON, leave as is
      }
    }
  }

  if (updated) {
    return newArgs;
  }

  return args;
}