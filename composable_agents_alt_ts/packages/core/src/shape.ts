import type { Node, Shape } from './types.js';
import { SHAPE_ORDER } from './types.js';

export function shapeRank(shape: Shape): number {
  return SHAPE_ORDER.indexOf(shape);
}

export function leqShape(a: Shape, b: Shape): boolean {
  return shapeRank(a) <= shapeRank(b);
}

export function joinShape(...shapes: Shape[]): Shape {
  if (shapes.length === 0) return 'Pipeline';
  return shapes.reduce((max, s) => (shapeRank(s) > shapeRank(max) ? s : max), 'Pipeline' as Shape);
}

export function surfaceShape(n: Node): Shape {
  switch (n.op) {
    case 'ident':
    case 'arr':
    case 'prim':
      return 'Pipeline';
    case 'seq':
      return joinShape(surfaceShape(req(n.left, n, 'left')), surfaceShape(req(n.right, n, 'right')));
    case 'par':
      return joinShape('Dataflow', surfaceShape(req(n.left, n, 'left')), surfaceShape(req(n.right, n, 'right')));
    case 'alt':
      return joinShape('Branching', surfaceShape(req(n.left, n, 'left')), surfaceShape(req(n.right, n, 'right')));
    case 'iter_up_to':
      return joinShape('Feedback', surfaceShape(req(n.body, n, 'body')));
    case 'eval_plan':
      return 'Staged';
    case 'app':
      return 'Agent';
    default:
      return assertNever(n.op);
  }
}

export function closedShape(n: Node): Shape {
  if (n.op === 'prim' && n.step?.kind === 'sub') return n.step.contract.shape;
  switch (n.op) {
    case 'ident':
    case 'arr':
    case 'prim':
      return 'Pipeline';
    case 'seq':
      return joinShape(closedShape(req(n.left, n, 'left')), closedShape(req(n.right, n, 'right')));
    case 'par':
      return joinShape('Dataflow', closedShape(req(n.left, n, 'left')), closedShape(req(n.right, n, 'right')));
    case 'alt':
      return joinShape('Branching', closedShape(req(n.left, n, 'left')), closedShape(req(n.right, n, 'right')));
    case 'iter_up_to':
      return joinShape('Feedback', closedShape(req(n.body, n, 'body')));
    case 'eval_plan':
      return 'Staged';
    case 'app':
      return 'Agent';
    default:
      return assertNever(n.op);
  }
}

function req<T>(v: T | undefined, n: Node, field: string): T {
  if (v === undefined) throw new Error(`Malformed node ${n.id}: missing ${field}`);
  return v;
}

function assertNever(x: never): never {
  throw new Error(`Unexpected op: ${x}`);
}
