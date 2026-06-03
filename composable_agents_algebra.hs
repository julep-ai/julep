{-# LANGUAGE GADTs #-}
-- Composable, Algebraic Agents — revised cut (v2; pseudo-Haskell, illustrative, not meant to compile)
--
-- THESIS (sharpened): agents and workflows differ by WHO OWNS THE CONTINUATION.
--   workflow         : the continuation lives in the static control graph
--   dynamic workflow : the continuation is synthesized ONCE into a reified Plan, then the runtime owns it
--   agent            : the continuation stays under online model control
-- Managed Agents supply the deployment boundary (brains / hands / sessions / events / isolated
-- subagents); this calculus exposes exactly those boundaries and no more.
--
-- WHAT CHANGED FROM v1 (and why):
--   * Tier -> Shape. We never measured determinism. A Think is stochastic, a Call can fail — none of
--     that changes whether the CONTROL TOPOLOGY is schedulable. Shape measures schedulability.
--   * + Staged / Plan. Dynamic workflows are NOT App: the script is generated, frozen, inspectable,
--     rerunnable, and a runtime (not the model turn-by-turn) owns the loop. That is its own shape.
--   * Think carries its context dependency explicitly (no hidden global session read), so :*** is
--     honestly parallel and the Session can be a partial order.
--   * Bounded loops are schedulable, not success-total (IterUpTo returns Either).
--   * Tools are typed up top, erased to the universal hand interface at the boundary.

module AlgebraicAgents where

type Name   = String
type NodeId = String
type CallId = String
data Value                                  -- opaque payloads at the boundary
data Schema a                               -- output-format / input type of a primitive
data Crit                                   -- a critique / correction carrier (loop state)


-- ============================================================
-- Shape — control-topology schedulability (NOT determinism)
-- ============================================================
data Shape
  = Pipeline    -- static sequence
  | Dataflow    -- static independent product / fanout
  | Branching   -- finite, known branch universe
  | Feedback    -- statically bounded recurrence
  | Staged      -- runtime-generated, then FROZEN, schedulable workflow   (dynamic workflow)
  | Agent       -- online synthesized continuation / unbounded control
  deriving (Eq, Ord, Show)
-- cuts:  buildTimeWorkflow = shape <= Feedback ;  dynamicWorkflow = Staged ;  onlineAgent = Agent


-- ============================================================
-- Primitives  (typed up top; the "hole" is the awaited result slot)
-- Step is profunctor-SHAPED (an input slot + an output slot). It is NOT itself a lawful
-- profunctor; the free arrow over Step supplies the compositional structure.
-- ============================================================
data Tool  i o = Tool  { toolName :: Name, inSchema :: Schema i, outSchema :: Schema o }
data Brain x y = Brain { brainName :: Name, promptSchema :: Schema x
                       , replySchema :: Schema y, ctxPolicy :: ContextPolicy }

-- The model's dependency on prior context is DECLARED, not smuggled in from global state.
data ContextPolicy = NoCtx | LocalThreadCtx | ParentSummaryCtx | WholeSessionCtx
  deriving (Eq, Ord, Show)

data    AgentRef x y  = AgentRef Name
newtype AgentContract = AgentContract { contractShape :: Shape }   -- what a sub promises, opaquely

data Step x y where
  Call  :: Tool  i o -> Step i o                       -- run a hand; the Output is the hole
  Think :: Brain x y -> Step x y                       -- model fills a typed hole from x + declared ctx
  Sub   :: AgentRef x y -> AgentContract -> Step x y   -- contract-bound delegation (closure)


-- ============================================================
-- Flow — the control algebra.  Shape = which constructors a term uses.
-- INVARIANT: Flow values are FINITE syntax trees. Recursion enters ONLY through IterUpTo (bounded),
-- EvalPlan (reified), or App (online) — never through host-language knots (let f = f :>>> g ...).
-- ============================================================
-- Pure glue is NAMED so it can be shipped/inspected, not an opaque host closure.
data Pure x y = Pure { pureName :: Name, runPure :: x -> y }

-- A Plan is a finite, generated, inspectable workflow artifact.
-- INVARIANT: surfaceShape (unPlan p) <= Feedback  (its own wiring is a workflow); it MAY still
-- contain Sub nodes whose contracts are Agent — closedShape sees through to those.
newtype Plan x y = Plan { unPlan :: Flow x y }

-- Operational facts ride as annotations; they NEVER alter control shape. (cost/risk/cache/effect/...)
data Annotation = Annotation { costHint, riskHint, cacheHint, effectHint, timeout :: Maybe Value }
noAnn :: Annotation
noAnn = Annotation Nothing Nothing Nothing Nothing Nothing

data Flow x y where
  Prim     :: NodeId -> Annotation -> Step x y -> Flow x y
  Ident    :: Flow x x
  Arr      :: Pure x y -> Flow x y
  (:>>>)   :: Flow x y -> Flow y z -> Flow x z
  (:***)   :: Flow a b -> Flow c d -> Flow (a, c) (b, d)
  (:|||)   :: Flow a z -> Flow b z -> Flow (Either a b) z
  IterUpTo :: Word -> Flow (a, s) (Either s b) -> Flow (a, s) (Either s b)  -- bounded; NOT success-total
  EvalPlan :: Flow (Plan a b, a) b           -- generated-then-frozen workflow   => Staged
  App      :: Flow (Flow a b, a) b           -- online arbitrary continuation     => Agent


-- ============================================================
-- Shape analysis — two readings of the same term.
--   surfaceShape : Sub is OPAQUE (parent stays schedulable regardless of child internals).
--   closedShape  : Sub contributes its contract shape (the deployment may host an agent).
-- A parent can be a surface workflow while closing over an agent behind a Sub. Feature, not bug.
-- ============================================================
surfaceShape :: Flow x y -> Shape
surfaceShape f = case f of
  Prim _ _ _   -> Pipeline                   -- includes Sub: opaque at the surface
  Ident        -> Pipeline
  Arr _        -> Pipeline
  a :>>> b     -> surfaceShape a `max` surfaceShape b
  a :*** b     -> Dataflow  `max` surfaceShape a `max` surfaceShape b
  a :||| b     -> Branching `max` surfaceShape a `max` surfaceShape b
  IterUpTo _ g -> Feedback  `max` surfaceShape g
  EvalPlan     -> Staged
  App          -> Agent

closedShape :: Flow x y -> Shape
closedShape f = case f of
  Prim _ _ (Sub _ c) -> contractShape c      -- read the sub's promised shape
  Prim _ _ _         -> Pipeline
  Ident              -> Pipeline
  Arr _              -> Pipeline
  a :>>> b           -> closedShape a `max` closedShape b
  a :*** b           -> Dataflow  `max` closedShape a `max` closedShape b
  a :||| b           -> Branching `max` closedShape a `max` closedShape b
  IterUpTo _ g       -> Feedback  `max` closedShape g
  EvalPlan           -> Staged               -- static view; given a concrete Plan, recurse: closedShape (unPlan p)
  App                -> Agent

isBuildTimeWorkflow, isClosedWorkflow :: Flow x y -> Bool
isBuildTimeWorkflow = (<= Feedback) . surfaceShape
isClosedWorkflow    = (<= Feedback) . closedShape


-- ============================================================
-- Session — durable causal trace.  A free PARTIALLY-COMMUTATIVE monoid (a trace monoid / pomset):
-- independent branches have NO canonical left-before-right order. This is the honest upgrade of
-- v1's "free monoid" once :*** is real concurrency. Recovery folds the trace; the harness is cattle.
-- ============================================================
type EventId  = String
type ThreadId = String
newtype Session = Session [Event]            -- read as a pomset keyed by (eventId, causes)
data Event = Event
  { eventId :: EventId
  , node    :: NodeId
  , thread  :: ThreadId
  , causes  :: [EventId]                     -- causal parents = the partial order
  , kind    :: EventKind }
data EventKind
  = Planned CallId Name Value                -- INTENT logged before the effect (idempotent recovery)
  | Did     CallId Name Value Value
  | Asked   ContextPolicy
  | Said    Value
  | Joined  Value                            -- a child's SUMMARIZED result (not its scratch events)
  | Failed  Value


-- ============================================================
-- Harness — interpreter. Threads Hands (DI) and the trace.
-- Effectful calls are idempotent under replay via stable call ids + intent logging.
-- ============================================================
-- Hands take a CallId so replay can dedupe real-world side effects.
type Hands m = CallId -> Name -> Value -> m Value

run :: Monad m => Hands m -> Session -> Flow x y -> x -> m (y, Session)
run hs s flow x = case flow of

  Prim n _ (Call tool) -> do                 -- intent-log, then execute, unless already in the trace
    let cid = stableCallId n x
    case recall cid s of
      Just v  -> pure (out v, s)             -- replay hit: do NOT re-fire the effect
      Nothing -> do
        let s1 = append s (Planned cid (toolName tool) (box x))
        v <- hs cid (toolName tool) (box x)
        pure (out v, append s1 (Did cid (toolName tool) (box x) v))

  Prim _ _ (Think brain) -> do               -- context is the DECLARED projection, not a global read
    let ctx = project (ctxPolicy brain) s x
        s1  = append s (Asked (ctxPolicy brain))
    y <- decide brain x ctx
    pure (y, append s1 (Said (box y)))

  Prim n _ (Sub ref c) -> do                 -- child runs in its OWN session; parent sees a summary
    (y, child) <- runSub ref c x
    pure (y, append s (Joined (summarize child)))

  Ident        -> pure (x, s)
  Arr p        -> pure (runPure p x, s)
  a :>>> b     -> do (y, s1) <- run hs s a x; run hs s1 b y
  a :*** b     -> do                         -- independent BY CONSTRUCTION: fork, run, merge traces
        let (l, r) = x
        (bl, sl) <- run hs (fork "L" s) a l
        (br, sr) <- run hs (fork "R" s) b r
        pure ((bl, br), merge s sl sr)        -- merge = union of causal traces (partial order kept)
  a :||| b     -> either (run hs s a) (run hs s b) x
  IterUpTo k g -> iterUpTo hs s k g x
  EvalPlan     -> let (Plan p, a) = x in run hs s p a   -- runtime owns the FROZEN plan's loop
  App          -> let (g,      a) = x in run hs s g a   -- online: the next Flow arrived AS DATA

-- Reboot a crashed harness: same `run`; the replay cursor lives in `recall`, recovery is a fold.
wake :: Monad m => Hands m -> Flow x y -> Session -> x -> m (y, Session)
wake hs flow s x = run hs s flow x

-- LAW: a branch declaring WholeSessionCtx forfeits free parallelism; the analysis degrades that
-- :*** edge to sequential. Only NoCtx / LocalThreadCtx branches are freely parallelizable.

-- stubs (runtime concerns, deliberately outside the control algebra)
stableCallId :: NodeId -> x -> CallId;                                       stableCallId = undefined
recall    :: CallId -> Session -> Maybe Value;                               recall    = undefined
append    :: Session -> EventKind -> Session;                                append    = undefined
project   :: ContextPolicy -> Session -> x -> Value;                         project   = undefined
decide    :: Monad m => Brain x y -> x -> Value -> m y;                       decide    = undefined
runSub    :: Monad m => AgentRef x y -> AgentContract -> x -> m (y, Session); runSub    = undefined
summarize :: Session -> Value;                                               summarize = undefined
fork      :: ThreadId -> Session -> Session;                                 fork      = undefined
merge     :: Session -> Session -> Session -> Session;                       merge     = undefined
iterUpTo  :: Monad m => Hands m -> Session -> Word
          -> Flow (a, s) (Either s b) -> (a, s) -> m (Either s b, Session);  iterUpTo  = undefined
box :: x -> Value;  box = undefined
out :: Value -> o;  out = undefined


-- ============================================================
-- Combinator algebra — the named patterns (sharper than v1)
-- ============================================================
pipeline :: Flow x y -> Flow y z -> Flow x z
pipeline = (:>>>)

parallel :: Flow a b -> Flow c d -> Flow (a, c) (b, d)               -- scale-out
parallel = (:***)

fanout :: Flow a b -> Flow a c -> Flow a (b, c)
fanout f g = Arr (Pure "dup" (\a -> (a, a))) :>>> (f :*** g)

route :: Flow a (Either l r) -> Flow l z -> Flow r z -> Flow a z     -- finite specialization
route r l h = r :>>> (l :||| h)

critique :: Word -> Flow (a, Crit) (Either Crit b)
         -> Flow (a, Crit) (Either Crit b)                           -- bounded refinement
critique = IterUpTo

stage :: Flow p (Plan a b) -> Flow (p, a) b                          -- model-as-workflow-compiler
stage planner = (planner :*** Ident) :>>> EvalPlan

escalate :: Flow a (Flow a b) -> Flow a b                            -- model-as-online-controller
escalate chooser = fanout chooser Ident :>>> App

subagent :: AgentRef x y -> AgentContract -> Flow x y                -- contract-bound delegation
subagent ref c = Prim "sub" noAnn (Sub ref c)

-- vocabulary, by shape:
--   parallel = scale-out (Dataflow)      route    = finite specialization (Branching)
--   critique = bounded refinement (Feedback)
--   stage    = model writes a workflow, runtime freezes & runs it (Staged)  <- dynamic workflows
--   escalate = model keeps choosing the next arrow online (Agent)
--   subagent = contract-bound delegation (opaque at surface; closedShape reads its contract)


-- ============================================================
-- Laws / framing
-- ============================================================
-- 1. WHO OWNS THE CONTINUATION: workflow -> static graph; dynamic workflow -> a frozen Plan owned by
--    the runtime; agent -> the model, online. The Shape lattice is exactly this ownership axis.
-- 2. CONTEXT HONESTY: any read from global session state is a control dependency until DECLARED.
--    ctxPolicy makes it explicit; hidden global reads are the main source of semantic drift.
-- 3. :*** is independent BY CONSTRUCTION (forked sessions); WholeSessionCtx forfeits that.
-- 4. Bounded loops are schedulable, not success-total (IterUpTo returns Either).
-- 5. Effects are idempotent under replay (stable CallId + Planned-before-Did); recovery is a fold.
-- 6. Flow is FINITE syntax; recursion enters only via IterUpTo / EvalPlan / App.
-- 7. App is where static extraction stops (ArrowApply == Monad). EvalPlan is its safer cousin:
--    same runtime-control shape, but the data is a VALIDATED workflow artifact, not an arbitrary Flow.