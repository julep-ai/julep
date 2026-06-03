import type { Node } from './types.js';
import { arr, par, parallel, pipeline, think } from './dsl.js';

export function race(...branches: Node[]): Node {
  return annotate(parallel(...branches), { combiner: 'race', strategy: 'race' });
}

export function hedge(delayMs: number, primary: Node, fallback: Node): Node {
  return annotate(par(primary, fallback), { combiner: 'hedge', strategy: 'hedge', hedgeMs: delayMs, hedgeDelayMs: delayMs });
}

export function quorum(need: number, ...branches: Node[]): Node {
  if (need < 1 || need > branches.length) throw new Error(`quorum need=${need} invalid for ${branches.length} branches`);
  return annotate(parallel(...branches), { combiner: 'quorum', strategy: 'quorum', quorum: { need, total: branches.length } });
}

export function vote(brains: string[] | Node[], aggregatorPure = 'majorityVote'): Node {
  const calls = brains.map((b) => typeof b === 'string' ? think(b) : b);
  return pipeline(annotate(parallel(...calls), { combiner: 'vote', strategy: 'vote' }), arr(aggregatorPure));
}

export function review(main: Node, kOrReviewer: number | Node, reviewerBrain = 'reviewer'): Node {
  if (typeof kOrReviewer !== 'number') return pipeline(main, kOrReviewer);
  const reviewers = Array.from({ length: kOrReviewer }, (_, i) => think(reviewerBrain, { id: `review_${i}` }));
  return annotate(pipeline(main, parallel(...reviewers)), { combiner: 'review', strategy: 'review' });
}

export function mapN(worker: Node, n: number): Node {
  const branches = Array.from({ length: n }, (_, i) => ({ ...worker, id: `${worker.id}_map_${i}` }));
  return annotate(parallel(...branches), { combiner: 'mapN', strategy: 'mapN' });
}

export function mapReduce(mapper: Node, reducer: Node, n: number): Node {
  return pipeline(mapN(mapper, n), reducer);
}

export function humanGate(signalName: string, timeoutSeconds?: number): Node {
  return annotate(think(`human:${signalName}`), { combiner: 'humanGate', strategy: 'humanGate', humanGate: stripUndefined({ signalName, timeoutSeconds }) });
}

function annotate(n: Node, ann: NonNullable<Node['ann']>): Node {
  return { ...n, ann: { ...n.ann, ...ann } };
}

function stripUndefined<T extends Record<string, unknown>>(obj: T): T {
  for (const key of Object.keys(obj)) {
    if (obj[key] === undefined) delete obj[key];
  }
  return obj;
}
