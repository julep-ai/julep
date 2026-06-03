import type { Diagnostic, FrozenTool, Node, ToolManifest } from './types.js';
import { leqShape, surfaceShape } from './shape.js';
import { inferInputSchema, inferOutputSchema, isSchemaAssignable, schemaSummary } from './schema.js';
import { hasPure } from './pure.js';
import { getStepToolHash, nodeCombiner, nodeStopPure } from './util.js';
import { isRaceSafe } from './tool_contract.js';

export interface ValidateOptions {
  manifest?: ToolManifest;
  requireRegisteredPures?: boolean;
  pureNames?: Set<string> | string[];
  checkRaceAdmission?: boolean;
}

export function validate(flow: Node, options: ValidateOptions = {}): Diagnostic[] {
  const diags: Diagnostic[] = [];
  const seen = new WeakSet<object>();
  visit(flow, '$', seen, diags, options);
  return diags;
}

export function assertValid(flow: Node, options: ValidateOptions = {}): void {
  const diags = validate(flow, options);
  const errors = diags.filter((d) => d.severity === 'error');
  if (errors.length > 0) {
    throw new Error(errors.map((e) => `${e.code} at ${e.path}: ${e.message}`).join('\n'));
  }
}

function visit(node: Node, path: string, seen: WeakSet<object>, diags: Diagnostic[], options: ValidateOptions): void {
  if (seen.has(node)) {
    diags.push(err('E_CYCLE', 'IR must be a finite tree; host-language object cycles are not deployable.', path, node.id));
    return;
  }
  seen.add(node);

  switch (node.op) {
    case 'prim':
      validatePrim(node, path, diags, options);
      break;
    case 'ident':
      break;
    case 'arr':
      validatePure(node.pure, path, node.id, diags, options, 'arr requires a named pure transform.');
      break;
    case 'seq':
      validateBinary(node, path, diags);
      if (node.left) visit(node.left, `${path}.left`, seen, diags, options);
      if (node.right) visit(node.right, `${path}.right`, seen, diags, options);
      if (node.left && node.right && !isSchemaAssignable(inferOutputSchema(node.left, options.manifest), inferInputSchema(node.right, options.manifest))) {
        diags.push(err(
          'E_SCHEMA_EDGE',
          `seq edge is not schema-compatible: ${schemaSummary(inferOutputSchema(node.left, options.manifest))} is not assignable to ${schemaSummary(inferInputSchema(node.right, options.manifest))}.`,
          path,
          node.id
        ));
      }
      break;
    case 'par':
      validateBinary(node, path, diags);
      if (node.left) visit(node.left, `${path}.left`, seen, diags, options);
      if (node.right) visit(node.right, `${path}.right`, seen, diags, options);
      if (containsWholeSessionCtx(node.left) || containsWholeSessionCtx(node.right)) {
        diags.push(warn(
          'W_PAR_CTX_DEGRADE',
          'A par branch reads WholeSessionCtx. This fanout must be lowered to seq by the deploy planner to avoid unsafe concurrent session reads.',
          path,
          node.id,
          'Use explicit window/summary context, or accept sequential lowering.'
        ));
      }
      if (options.checkRaceAdmission !== false) validateRaceAdmission(node, path, diags, options.manifest);
      break;
    case 'alt':
      validatePure(node.pure, path, node.id, diags, options, 'alt requires a named pure predicate. Use think -> alt for model-judged routes.');
      validateBinary(node, path, diags);
      if (node.left) visit(node.left, `${path}.left`, seen, diags, options);
      if (node.right) visit(node.right, `${path}.right`, seen, diags, options);
      break;
    case 'iter_up_to': {
      if (node.bound === undefined || !Number.isInteger(node.bound) || node.bound < 1) {
        diags.push(err('E_LOOP_BOUND', 'iter_up_to requires a finite positive integer bound.', path, node.id));
      }
      const stop = nodeStopPure(node);
      if (stop) validatePure(stop, `${path}.stopPure`, node.id, diags, options, 'iter_up_to stopPure must be named.');
      requireChild(node.body, 'body', path, node.id, diags);
      if (node.body) visit(node.body, `${path}.body`, seen, diags, options);
      break;
    }
    case 'eval_plan':
      if (!node.plan && !node.controller) {
        diags.push(err('E_STAGE_MISSING_PLAN_OR_CONTROLLER', 'eval_plan needs either a static plan or a planner controller.', path, node.id));
      }
      if (node.plan) {
        visit(node.plan, `${path}.plan`, seen, diags, options);
        if (!leqShape(surfaceShape(node.plan), 'Feedback')) {
          diags.push(err('E_PLAN_SHAPE', `eval_plan payload must have surfaceShape <= Feedback; got ${surfaceShape(node.plan)}.`, `${path}.plan`, node.plan.id));
        }
      }
      break;
    case 'app':
      if (!node.controller) diags.push(err('E_APP_CONTROLLER', 'app requires a controller reference.', path, node.id));
      break;
    default:
      diags.push(err('E_UNKNOWN_OP', `Unknown op ${(node as Node).op}.`, path, node.id));
  }
}

function validatePrim(node: Node, path: string, diags: Diagnostic[], options: ValidateOptions): void {
  if (!node.step) {
    diags.push(err('E_PRIM_STEP', 'prim node requires a step.', path, node.id));
    return;
  }
  if (node.step.kind === 'call') {
    const hash = getStepToolHash(node.step);
    if (!hash) {
      diags.push(err('E_UNFROZEN_TOOL', 'call step has no toolHash/frozenHash; run freeze before deploy.', path, node.id));
    } else if (options.manifest && !options.manifest[hash]) {
      diags.push(err('E_TOOL_NOT_IN_MANIFEST', `tool hash ${hash} is missing from manifest.`, path, node.id));
    }
  }
  if (node.step.kind === 'think') {
    if (!node.step.brain) diags.push(err('E_BRAIN_REF', 'think step requires a brain reference.', path, node.id));
  }
  if (node.step.kind === 'sub') {
    if (!node.step.ref) diags.push(err('E_SUB_REF', 'sub step requires a workflow ref.', path, node.id));
    if (!node.step.contract?.shape) diags.push(err('E_SUB_CONTRACT', 'sub step requires a shape contract.', path, node.id));
  }
}

function validatePure(
  name: string | undefined,
  path: string,
  nodeId: string,
  diags: Diagnostic[],
  options: ValidateOptions,
  missingMessage: string
): void {
  if (!name) {
    diags.push(err('E_NAMED_PURE', missingMessage, path, nodeId));
    return;
  }
  if (!/^[-a-zA-Z0-9_./:@]+$/.test(name)) {
    diags.push(err('E_PURE_BAD_NAME', `pure name '${name}' is not registry-safe.`, path, nodeId));
  }
  const pureSet = options.pureNames ? new Set(Array.isArray(options.pureNames) ? options.pureNames : [...options.pureNames]) : undefined;
  if (pureSet && !pureSet.has(name)) {
    diags.push(err('E_PURE_NOT_REGISTERED', `Pure '${name}' is not in the supplied pure set.`, path, nodeId));
  }
  if (options.requireRegisteredPures && !hasPure(name)) {
    diags.push(err('E_PURE_NOT_REGISTERED', `Pure '${name}' is not registered in this process.`, path, nodeId));
  }
}

function validateBinary(node: Node, path: string, diags: Diagnostic[]): void {
  requireChild(node.left, 'left', path, node.id, diags);
  requireChild(node.right, 'right', path, node.id, diags);
}

function requireChild(child: Node | undefined, field: string, path: string, nodeId: string, diags: Diagnostic[]): void {
  if (!child) diags.push(err('E_MISSING_CHILD', `Missing ${field} child.`, `${path}.${field}`, nodeId));
}

function containsWholeSessionCtx(node: Node | undefined): boolean {
  if (!node) return false;
  const stepCtx = node.step && 'ctx' in node.step ? node.step.ctx : undefined;
  if (stepCtx?.kind === 'whole_session') return true;
  return containsWholeSessionCtx(node.left) || containsWholeSessionCtx(node.right) || containsWholeSessionCtx(node.body) || containsWholeSessionCtx(node.plan);
}

function validateRaceAdmission(node: Node, path: string, diags: Diagnostic[], manifest?: ToolManifest): void {
  const combiner = nodeCombiner(node.ann);
  if (!combiner || !['race', 'hedge', 'quorum'].includes(combiner)) return;
  for (const leaf of callLeaves(node)) {
    const hash = leaf.step?.kind === 'call' ? getStepToolHash(leaf.step) : undefined;
    const tool = hash ? manifest?.[hash] : undefined;
    if (!tool) {
      diags.push(err('E_RACE_TOOL_NOT_FROZEN', 'race/hedge/quorum branch contains an unresolved tool.', path, leaf.id));
      continue;
    }
    if (!isRaceAdmissible(tool)) {
      diags.push(err(
        'E_RACE_ADMISSION',
        `${combiner} branch uses ${toolLabel(tool)}, but only read tools or asserted native/required idempotent tools are admitted.`,
        path,
        leaf.id
      ));
    }
  }
}

function isRaceAdmissible(tool: FrozenTool): boolean {
  if (!tool.contract.asserted && tool.contract.idempotency === 'none') return false;
  return isRaceSafe(tool.contract);
}

function callLeaves(node: Node): Node[] {
  if (node.op === 'prim' && node.step?.kind === 'call') return [node];
  return [node.left, node.right, node.body, node.plan].filter((x): x is Node => Boolean(x)).flatMap(callLeaves);
}

function toolLabel(tool: FrozenTool): string {
  return tool.ref.kind === 'native' ? tool.ref.name : `${tool.ref.server}/${tool.ref.tool}`;
}

function err(code: string, message: string, path: string, nodeId?: string): Diagnostic {
  return stripUndefined({ severity: 'error' as const, code, message, path, nodeId });
}

function warn(code: string, message: string, path: string, nodeId?: string, fix?: string): Diagnostic {
  return stripUndefined({ severity: 'warning' as const, code, message, path, nodeId, fix });
}

function stripUndefined<T extends Record<string, unknown>>(obj: T): T {
  for (const key of Object.keys(obj)) {
    if (obj[key] === undefined) delete obj[key];
  }
  return obj;
}
