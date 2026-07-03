"""Local session primitives (cata inside / ana outside, design §4).

A session wraps an ordinary finite turn flow inside an unbounded ``Op.LOOP`` IR
boundary. The interpreter remains the catamorphism over the turn; this module
provides the local in-memory anamorphism that feeds messages in, threads the
carrier, and collects emitted outputs.
"""

from __future__ import annotations

import asyncio
import ast
import copy
import hashlib
import inspect
import textwrap
from dataclasses import dataclass
from collections.abc import AsyncIterator, Callable
from itertools import islice
from typing import Any, Generic, Iterable, Optional, Protocol, TypeVar, cast, overload

from .dsl import _nid, _node
from .errors import ComposableAgentsError, SessionTurnError
from .ir import ChannelRef, JSONSchema, Node
from .kinds import EnforcementMode, Op
from .execution.interpreter import InMemoryEnv, SessionClosed, interpret
from .projection import InMemoryProjection, ProjectionEmitter

InT = TypeVar("InT")
OutT = TypeVar("OutT")
T = TypeVar("T")


def _local_value_fingerprint(value: Any) -> str:
    try:
        from .execution.session_store import value_fingerprint

        return value_fingerprint(value)
    except Exception:
        return repr(value)


class Channel(Generic[T]):
    """A typed in-memory session port."""

    name: str
    payload: Optional[JSONSchema]

    def __init__(self, name: str, payload: Optional[JSONSchema] = None) -> None:
        self.name = name
        self.payload = payload
        self._inbound: asyncio.Queue[T] = asyncio.Queue()
        self._outbound: list[object] = []

    async def recv(self) -> T:
        """Take the next inbound message from the channel FIFO."""
        return await self._inbound.get()

    def append(self, value: T) -> None:
        """Append an inbound message to the channel FIFO."""
        self._inbound.put_nowait(value)

    def emit(self, value: object) -> None:
        """Append an outbound value to this channel's output buffer."""
        self._outbound.append(value)

    def drain(self) -> list[object]:
        """Return and clear the outbound output buffer."""
        out = list(self._outbound)
        self._outbound.clear()
        return out


@dataclass
class Session(Generic[InT, OutT]):
    """A typed handle for a LOOP body and its local carrier state."""

    body: Node
    init: object
    in_channel: str
    out_channel: str


@dataclass(frozen=True)
class SessionEvent:
    """A normalized event from a live session."""

    kind: str
    channel: Optional[str] = None
    seq: Optional[int] = None
    payload: Any = None
    turn: Optional[str] = None
    reason: Optional[str] = None
    fatal: bool = False

    @classmethod
    def emit(cls, channel: str, seq: int, payload: Any) -> "SessionEvent":
        return cls(kind="emit", channel=channel, seq=seq, payload=payload)

    @classmethod
    def turn_started(cls) -> "SessionEvent":
        return cls(kind="turn", turn="started")

    @classmethod
    def turn_done(cls) -> "SessionEvent":
        return cls(kind="turn", turn="done")

    @classmethod
    def error(cls, reason: str, *, fatal: bool) -> "SessionEvent":
        return cls(kind="error", reason=reason, fatal=fatal)

    @classmethod
    def closed(cls, reason: Optional[str] = None) -> "SessionEvent":
        return cls(kind="closed", reason=reason)

    @property
    def is_emit(self) -> bool:
        return self.kind == "emit"

    @property
    def is_turn(self) -> bool:
        return self.kind == "turn"

    @property
    def is_error(self) -> bool:
        return self.kind == "error"

    @property
    def is_closed(self) -> bool:
        return self.kind == "closed"


class SessionHandle(Protocol):
    """A live session facade shared by local and Temporal backends."""

    def events(self) -> AsyncIterator[SessionEvent]: ...

    async def send(
        self,
        value: Any,
        *,
        channel: Optional[str] = None,
        idempotency_key: Any = None,
    ) -> dict[str, Any]: ...

    async def state(self) -> dict[str, Any]: ...

    async def open_receives(self) -> list[dict[str, Any]]: ...

    async def close(self, reason: Optional[str] = None) -> None: ...


class SessionValidationError(ComposableAgentsError):
    """Raised when a public session constructor receives an unsafe LOOP body."""


class SessionCompileError(ComposableAgentsError):
    """Raised when ``@session`` coroutine sugar cannot be safely lifted."""


def scan(
    step_flow: Node,
    init: object,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any]:
    """Wrap ``step_flow`` as the turn body of a session LOOP."""
    loop_node = _loop_node(
        step_flow,
        in_channel=in_channel,
        out_channel=out_channel,
        state_schema=state_schema,
        split=True,
    )
    _raise_on_blocking_session_diagnostics(loop_node)
    return Session(
        body=loop_node,
        init=init,
        in_channel=in_channel,
        out_channel=out_channel,
    )


@overload
def session(
    func: Callable[..., Any],
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any]: ...


@overload
def session(
    func: None = None,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Callable[[Callable[..., Any]], Session[Any, Any]]: ...


def session(
    func: Optional[Callable[..., Any]] = None,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any] | Callable[[Callable[..., Any]], Session[Any, Any]]:
    """EXPERIMENTAL: lift a straight-line async turn loop into ``scan(...)``.

    The accepted shape is intentionally narrow: pre-loop assignments followed
    by a final ``while True`` whose body receives once via ``await s.recv()``,
    emits once via ``await s.emit(value)``, and reassigns carried locals.
    Non-liftable functions should be expressed explicitly with ``scan(step, init)``.
    """

    def decorate(inner: Callable[..., Any]) -> Session[Any, Any]:
        return _compile_session_function(
            inner,
            in_channel=in_channel,
            out_channel=out_channel,
            state_schema=state_schema,
        )

    if func is None:
        return decorate
    return decorate(func)


def _session_compile_error(reason: str) -> SessionCompileError:
    return SessionCompileError(
        f"cannot compile @session coroutine: {reason}. "
        "Declare the session explicitly with scan(step, init)."
    )


def _compile_session_function(
    func: Callable[..., Any],
    *,
    in_channel: str,
    out_channel: str,
    state_schema: Optional[JSONSchema],
) -> Session[Any, Any]:
    from .derived import recv
    from .dsl import arr, seq
    from .purity import register_pure_with_source

    parsed = _ParsedSession.from_function(func)
    init = parsed.build_init(func)
    step, canonical_source = parsed.build_step(
        func,
        in_channel=in_channel,
        out_channel=out_channel,
    )
    short_hash = hashlib.sha256(canonical_source.encode("utf-8")).hexdigest()[:12]
    pure_name = f"session.{func.__module__}.{func.__qualname__}.{short_hash}"
    register_pure_with_source(pure_name, step, canonical_source)
    return scan(
        seq(recv(in_channel), arr(pure_name)),
        init=init,
        in_channel=in_channel,
        out_channel=out_channel,
        state_schema=state_schema,
    )


@dataclass(frozen=True)
class _ParsedSession:
    pre_loop: list[ast.stmt]
    loop_body: list[ast.stmt]
    session_arg: str
    recv_target: str
    carried_names: tuple[str, ...]
    filename: str

    @classmethod
    def from_function(cls, func: Callable[..., Any]) -> "_ParsedSession":
        if not inspect.iscoroutinefunction(func):
            raise _session_compile_error("decorated object must be an async def")
        try:
            source = inspect.getsource(func)
        except (OSError, TypeError) as exc:
            raise _session_compile_error(
                "source is unavailable for AST lifting"
            ) from exc

        module = ast.parse(textwrap.dedent(source))
        fn = _find_async_function(module, func.__name__)
        if fn is None:
            raise _session_compile_error("could not find the async function body")
        session_arg = _session_arg_name(fn)
        body = _strip_docstring(fn.body)
        if not body or not isinstance(body[-1], ast.While):
            raise _session_compile_error(
                "body must be pre-loop assignments followed by a final while True"
            )
        if len([stmt for stmt in body if isinstance(stmt, ast.While)]) != 1:
            raise _session_compile_error("body must contain exactly one while True loop")

        pre_loop = list(body[:-1])
        loop = body[-1]
        if not _is_literal_true(loop.test):
            raise _session_compile_error("the loop test must be literal True")
        if loop.orelse:
            raise _session_compile_error("while True loops with else blocks are not liftable")
        if not all(_is_simple_pre_loop_assign(stmt) for stmt in pre_loop):
            raise _session_compile_error(
                "pre-loop code must be simple assignments that compute init"
            )

        loop_body = list(loop.body)
        recv_target = _recv_target(loop_body[0] if loop_body else None, session_arg)
        recv_count = _count_awaited_calls(loop_body, session_arg, "recv")
        if recv_count != 1:
            raise _session_compile_error(
                f"loop body must contain exactly one await {session_arg}.recv() call"
            )
        emit_count = _count_awaited_calls(loop_body, session_arg, "emit")
        if emit_count != 1:
            raise _session_compile_error(
                f"loop body must contain exactly one await {session_arg}.emit(...) call"
            )
        if _contains_control_flow(loop_body):
            raise _session_compile_error(
                "loop body must be straight-line code around recv and emit"
            )

        pre_names = _assigned_names(pre_loop)
        referenced_after_recv = _referenced_names(loop_body[1:])
        carried = tuple(
            name
            for name in pre_names
            if name in referenced_after_recv and name != recv_target
        )
        if _nested_captures(loop_body, set(carried)):
            raise _session_compile_error(
                "a carried local is captured by a nested function or lambda"
            )

        transformed = _transform_loop_body(loop_body, session_arg)
        if _contains_await(transformed[1:]):
            raise _session_compile_error(
                "only recv and emit awaits are supported in @session loop bodies"
            )

        return cls(
            pre_loop=pre_loop,
            loop_body=transformed,
            session_arg=session_arg,
            recv_target=recv_target,
            carried_names=carried,
            filename=inspect.getsourcefile(func) or "<session>",
        )

    def build_init(self, func: Callable[..., Any]) -> object:
        name = "__session_init__"
        body = [copy.deepcopy(stmt) for stmt in self.pre_loop]
        body.append(ast.Return(value=self._carrier_expr()))
        init_fn = ast.FunctionDef(
            name=name,
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=body or [ast.Return(value=ast.Constant(value=None))],
            decorator_list=[],
        )
        namespace = _exec_namespace(func)
        module = ast.fix_missing_locations(ast.Module(body=[init_fn], type_ignores=[]))
        exec(compile(module, self.filename, "exec"), namespace)
        result = namespace[name]()
        return result

    def build_step(
        self,
        func: Callable[..., Any],
        *,
        in_channel: str,
        out_channel: str,
    ) -> tuple[Callable[[dict[str, Any]], tuple[object, object]], str]:
        name = "__session_step__"
        body: list[ast.stmt] = [
            ast.Assign(
                targets=[ast.Name(id="__carrier", ctx=ast.Store())],
                value=ast.Subscript(
                    value=ast.Name(id="__value", ctx=ast.Load()),
                    slice=ast.Constant(value="carrier"),
                    ctx=ast.Load(),
                ),
            ),
            ast.Assign(
                targets=[ast.Name(id="__msg", ctx=ast.Store())],
                value=ast.Subscript(
                    value=ast.Name(id="__value", ctx=ast.Load()),
                    slice=ast.Constant(value="msg"),
                    ctx=ast.Load(),
                ),
            ),
        ]
        body.extend(self._carrier_unpack_stmts())
        body.append(
            ast.Assign(
                targets=[ast.Name(id=self.recv_target, ctx=ast.Store())],
                value=ast.Name(id="__msg", ctx=ast.Load()),
            )
        )
        body.extend(copy.deepcopy(self.loop_body[1:]))
        body.append(
            ast.Return(
                value=ast.Tuple(
                    elts=[
                        self._carrier_expr(),
                        ast.Name(id="__session_output", ctx=ast.Load()),
                    ],
                    ctx=ast.Load(),
                )
            )
        )
        step_fn = ast.FunctionDef(
            name=name,
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="__value")],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=body,
            decorator_list=[],
        )
        namespace = _exec_namespace(func)
        module = ast.fix_missing_locations(ast.Module(body=[step_fn], type_ignores=[]))
        fixed_step = cast(ast.FunctionDef, module.body[0])
        canonical_source = _canonical_step_source(
            fixed_step,
            carried_names=self.carried_names,
            in_channel=in_channel,
            out_channel=out_channel,
        )
        exec(compile(module, self.filename, "exec"), namespace)
        step = cast(Callable[[dict[str, Any]], tuple[object, object]], namespace[name])
        if not callable(step):
            raise _session_compile_error("generated step pure is not callable")
        return step, canonical_source

    def _carrier_expr(self) -> ast.expr:
        if not self.carried_names:
            return ast.Constant(value=None)
        if len(self.carried_names) == 1:
            return ast.Name(id=self.carried_names[0], ctx=ast.Load())
        return ast.Tuple(
            elts=[ast.Name(id=name, ctx=ast.Load()) for name in self.carried_names],
            ctx=ast.Load(),
        )

    def _carrier_unpack_stmts(self) -> list[ast.stmt]:
        if not self.carried_names:
            return []
        if len(self.carried_names) == 1:
            return [
                ast.Assign(
                    targets=[ast.Name(id=self.carried_names[0], ctx=ast.Store())],
                    value=ast.Name(id="__carrier", ctx=ast.Load()),
                )
            ]
        return [
            ast.Assign(
                targets=[
                    ast.Tuple(
                        elts=[
                            ast.Name(id=name, ctx=ast.Store())
                            for name in self.carried_names
                        ],
                        ctx=ast.Store(),
                    )
                ],
                value=ast.Name(id="__carrier", ctx=ast.Load()),
            )
        ]


def _canonical_step_source(
    step_fn: ast.FunctionDef,
    *,
    carried_names: tuple[str, ...],
    in_channel: str,
    out_channel: str,
) -> str:
    return (
        ast.unparse(step_fn)
        + "\n"
        + f"# session_carried_names={carried_names!r}\n"
        + f"# session_in_channel={in_channel!r}\n"
        + f"# session_out_channel={out_channel!r}\n"
    )


def _exec_namespace(func: Callable[..., Any]) -> dict[str, Any]:
    namespace = dict(func.__globals__)
    closure = inspect.getclosurevars(func)
    namespace.update(closure.globals)
    namespace.update(closure.nonlocals)
    return namespace


def _find_async_function(module: ast.Module, name: str) -> Optional[ast.AsyncFunctionDef]:
    for node in module.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            return node
    for walked in ast.walk(module):
        if isinstance(walked, ast.AsyncFunctionDef) and walked.name == name:
            return walked
    return None


def _session_arg_name(fn: ast.AsyncFunctionDef) -> str:
    args = fn.args
    if (
        args.posonlyargs
        or len(args.args) != 1
        or args.vararg is not None
        or args.kwonlyargs
        or args.kwarg is not None
    ):
        raise _session_compile_error("async session functions must accept exactly one parameter")
    return args.args[0].arg


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _is_literal_true(expr: ast.expr) -> bool:
    return isinstance(expr, ast.Constant) and expr.value is True


def _is_simple_pre_loop_assign(stmt: ast.stmt) -> bool:
    if isinstance(stmt, ast.Assign):
        return all(isinstance(target, ast.Name) for target in stmt.targets)
    if isinstance(stmt, ast.AnnAssign):
        return isinstance(stmt.target, ast.Name) and stmt.value is not None
    return False


def _recv_target(stmt: Optional[ast.stmt], session_arg: str) -> str:
    value: ast.expr
    target: ast.expr
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        target = stmt.targets[0]
        value = stmt.value
    elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        target = stmt.target
        value = stmt.value
    else:
        raise _session_compile_error(
            f"first loop statement must assign await {session_arg}.recv() to a name"
        )
    if not isinstance(target, ast.Name):
        raise _session_compile_error("recv target must be a single local name")
    if not _is_awaited_call(value, session_arg, "recv"):
        raise _session_compile_error(
            f"first loop statement must assign await {session_arg}.recv() to a name"
        )
    return target.id


def _is_awaited_call(expr: ast.AST, session_arg: str, method: str) -> bool:
    if not isinstance(expr, ast.Await):
        return False
    call = expr.value
    return _is_session_call(call, session_arg, method)


def _is_session_call(node: ast.AST, session_arg: str, method: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == method
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == session_arg
    )


def _count_awaited_calls(stmts: list[ast.stmt], session_arg: str, method: str) -> int:
    count = 0
    for node in _walk_without_nested_defs(stmts):
        if isinstance(node, ast.Await) and _is_session_call(node.value, session_arg, method):
            count += 1
    return count


def _contains_control_flow(stmts: list[ast.stmt]) -> bool:
    control_flow = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)
    for node in _walk_without_nested_defs(stmts):
        if isinstance(node, control_flow):
            return True
    return False


def _contains_await(stmts: list[ast.stmt]) -> bool:
    return any(isinstance(node, ast.Await) for node in _walk_without_nested_defs(stmts))


def _walk_without_nested_defs(stmts: list[ast.stmt]) -> list[ast.AST]:
    out: list[ast.AST] = []

    class Visitor(ast.NodeVisitor):
        def generic_visit(self, node: ast.AST) -> None:
            out.append(node)
            super().generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            out.append(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            out.append(node)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            out.append(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            out.append(node)

    visitor = Visitor()
    for stmt in stmts:
        visitor.visit(stmt)
    return out


def _assigned_names(stmts: list[ast.stmt]) -> tuple[str, ...]:
    names: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            names.append(node.name)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            names.append(node.name)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            del node

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            names.append(node.name)

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, ast.Store) and node.id not in names:
                names.append(node.id)

    visitor = Visitor()
    for stmt in stmts:
        visitor.visit(stmt)
    return tuple(names)


def _referenced_names(stmts: list[ast.stmt]) -> set[str]:
    names: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, (ast.Load, ast.Store)):
                names.add(node.id)

    visitor = Visitor()
    for stmt in stmts:
        visitor.visit(stmt)
    return names


def _nested_captures(stmts: list[ast.stmt], carried: set[str]) -> bool:
    if not carried:
        return False
    for stmt in stmts:
        for node in ast.walk(stmt):
            nested_body: list[ast.stmt]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nested_body = list(node.body)
            elif isinstance(node, ast.Lambda):
                nested_body = [ast.Expr(value=node.body)]
            else:
                continue
            if _loaded_names_including_nested(nested_body) & carried:
                return True
    return False


def _loaded_names_including_nested(stmts: list[ast.stmt]) -> set[str]:
    names: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, ast.Load):
                names.add(node.id)

    visitor = Visitor()
    for stmt in stmts:
        visitor.visit(stmt)
    return names


def _transform_loop_body(stmts: list[ast.stmt], session_arg: str) -> list[ast.stmt]:
    return [_EmitTransformer(session_arg).visit_stmt(copy.deepcopy(stmt)) for stmt in stmts]


class _EmitTransformer(ast.NodeTransformer):
    def __init__(self, session_arg: str) -> None:
        self._session_arg = session_arg

    def visit_stmt(self, stmt: ast.stmt) -> ast.stmt:
        transformed = self.visit(stmt)
        if not isinstance(transformed, ast.stmt):
            raise _session_compile_error("loop body transformation produced invalid AST")
        return transformed

    def visit_Expr(self, node: ast.Expr) -> ast.stmt:
        if isinstance(node.value, ast.Await) and _is_session_call(
            node.value.value,
            self._session_arg,
            "emit",
        ):
            call = node.value.value
            if not isinstance(call, ast.Call):
                raise _session_compile_error("emit call could not be analyzed")
            return ast.Assign(
                targets=[ast.Name(id="__session_output", ctx=ast.Store())],
                value=_emit_value_expr(call),
            )
        transformed = self.generic_visit(node)
        if not isinstance(transformed, ast.stmt):
            raise _session_compile_error("loop body transformation produced invalid AST")
        return transformed


def _emit_value_expr(call: ast.Call) -> ast.expr:
    if call.args:
        if len(call.args) != 1:
            raise _session_compile_error("emit must be called with one value")
        return call.args[0]
    for keyword in call.keywords:
        if keyword.arg == "value":
            return keyword.value
    raise _session_compile_error("emit must be called with a value")


def loop(
    body: Node,
    *,
    init: object,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
) -> Session[Any, Any]:
    """Build a LOOP IR node around an already-authored turn body."""
    loop_node = _loop_node(
        body,
        in_channel=in_channel,
        out_channel=out_channel,
        state_schema=state_schema,
    )
    _raise_on_blocking_session_diagnostics(loop_node)
    return Session(
        body=loop_node,
        init=init,
        in_channel=in_channel,
        out_channel=out_channel,
    )


def _loop_node(
    body: Node,
    *,
    in_channel: str = "in",
    out_channel: str = "out",
    state_schema: Optional[JSONSchema] = None,
    split: bool = False,
) -> Node:
    """Build a LOOP node without running the public construction gate."""
    args = {"split": True} if split else None
    return _node(
        op=Op.LOOP,
        id=_nid("loop"),
        body=body,
        state_schema=state_schema,
        channels=[ChannelRef(in_channel), ChannelRef(out_channel)],
        args=args,
    )


def _raise_on_blocking_session_diagnostics(loop_node: Node) -> None:
    from .validate import blocking, validate

    # Enforce at construction rather than freeze time: deploy.py freezes before
    # validate, and session safety should not perturb that order.
    errors = [
        d
        for d in blocking(validate(loop_node))
        if d.code.startswith("SESSION_")
    ]
    if not errors:
        return
    details = "; ".join(f"{d.code}: {d.message}" for d in errors)
    raise SessionValidationError(f"invalid session LOOP: {details}")


async def drive_session(
    session: Session[InT, OutT],
    *,
    inputs: Iterable[InT],
    max_turns: int = 1000,
    env: Optional[InMemoryEnv] = None,
) -> tuple[object, list[OutT]]:
    """Run a session LOOP over in-memory channel input and collect emissions."""
    messages = list(islice(inputs, max(0, max_turns + 1)))
    if len(messages) > max_turns:
        raise ComposableAgentsError(
            f"session consumed more than {max_turns} messages"
        )
    if env is None:
        env = InMemoryEnv(
            {},
            ProjectionEmitter(InMemoryProjection()),
            inbound={session.in_channel: messages},
        )
    result = await interpret(session.body, session.init, env)
    return result.value, env.emitted(session.out_channel)


class _LiveLocalEnv(InMemoryEnv):
    """Channel-backed in-memory env for a long-lived local session."""

    _WAKE: object = object()

    def __init__(
        self,
        *args: Any,
        event_queue: asyncio.Queue[SessionEvent],
        channel_capacity: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._event_queue = event_queue
        self._live_inbound: dict[str, asyncio.Queue[Any]] = {}
        self._live_emitted: dict[str, list[dict[str, Any]]] = {}
        self._live_seq: dict[str, int] = {}
        self._open_recv: dict[str, int] = {}
        self._capacity = channel_capacity
        self._live_closed = False
        self._turn_started = False

    def _queue(self, channel: str) -> asyncio.Queue[Any]:
        return self._live_inbound.setdefault(channel, asyncio.Queue())

    def close_channels(self) -> None:
        self._live_closed = True
        for queue in self._live_inbound.values():
            queue.put_nowait(self._WAKE)

    def append_live(self, channel: str, value: Any) -> int:
        queue = self._queue(channel)
        seq = self._live_seq.get(f"in:{channel}", 0) + 1
        self._live_seq[f"in:{channel}"] = seq
        queue.put_nowait(value)
        return seq

    async def recv(self, channel: str, cid: str, timeout_s: Optional[int]) -> Any:
        del cid, timeout_s
        queue = self._queue(channel)
        while True:
            if self._live_closed and queue.empty():
                raise SessionClosed(f"session channel {channel!r} is closed")
            self._open_recv[channel] = (
                self._live_seq.get(f"consumed:{channel}", 0) + 1
            )
            try:
                item = await queue.get()
            finally:
                self._open_recv.pop(channel, None)
            if item is self._WAKE:
                if self._live_closed and queue.empty():
                    raise SessionClosed(f"session channel {channel!r} is closed")
                continue
            consumed = self._live_seq.get(f"consumed:{channel}", 0) + 1
            self._live_seq[f"consumed:{channel}"] = consumed
            self._turn_started = True
            await self._event_queue.put(SessionEvent.turn_started())
            return item

    async def emit(self, channel: str, value: Any, cid: str) -> None:
        del cid
        seq = self._live_seq.get(f"out:{channel}", 0) + 1
        self._live_seq[f"out:{channel}"] = seq
        item = {"seq": seq, "payload": value}
        self._live_emitted.setdefault(channel, []).append(item)
        await self._event_queue.put(SessionEvent.emit(channel, seq, value))

    def emitted_records(self) -> dict[str, list[dict[str, Any]]]:
        return {
            channel: [dict(item) for item in items]
            for channel, items in self._live_emitted.items()
        }

    def evict_emit(self, channel: str, seq: Optional[int]) -> None:
        if seq is None:
            return
        self._live_emitted[channel] = [
            item
            for item in self._live_emitted.get(channel, [])
            if int(item.get("seq", 0)) != seq
        ]

    def pending_counts(self) -> dict[str, int]:
        return {
            channel: queue.qsize()
            for channel, queue in self._live_inbound.items()
        }

    def pending_count(self, channel: str) -> int:
        return self._queue(channel).qsize()

    def capacity(self) -> Optional[int]:
        return self._capacity

    def open_receives_records(self) -> list[dict[str, Any]]:
        # cid is deferred to match the current workflow query shape.
        return [
            {"channel": channel, "seq": seq}
            for channel, seq in sorted(self._open_recv.items())
        ]

    def take_turn_started(self) -> bool:
        started = self._turn_started
        self._turn_started = False
        return started


class LocalSessionHandle:
    """In-memory live session handle."""

    def __init__(
        self,
        session: Session[Any, Any],
        env: _LiveLocalEnv,
        *,
        max_turns: int,
        max_consecutive_turn_errors: int = 3,
        reason: Optional[str] = None,
    ) -> None:
        self._session = session
        self._env = env
        self._events: asyncio.Queue[SessionEvent] = env._event_queue
        self._max_turns = max_turns
        self._max_consecutive_turn_errors = max_consecutive_turn_errors
        self._carrier = session.init
        self._closed = False
        self._close_reason = reason
        self._done = asyncio.Event()
        self._closed_event_sent = False
        self._driver_exc: Optional[BaseException] = None
        self._events_subscribed = False
        self._idem: dict[str, dict[str, tuple[int, str]]] = {}
        self._driver = asyncio.create_task(self._drive())

    @classmethod
    async def open(
        cls,
        session: Session[Any, Any],
        *,
        tools: Optional[dict[str, Callable[[Any], Any]]] = None,
        reasoners: Optional[dict[str, Callable[[Any], Any]]] = None,
        subs: Optional[dict[str, Callable[[Any], Any]]] = None,
        agents: Optional[dict[str, Callable[[Any], Any]]] = None,
        planners: Optional[dict[str, Callable[[Any], Node]]] = None,
        max_calls: Optional[dict[str, int]] = None,
        mode: EnforcementMode | str = EnforcementMode.STRICT,
        principal: Optional[dict[str, Any]] = None,
        max_turns: int = 100000,
        max_consecutive_turn_errors: int = 3,
        channel_capacity: Optional[int] = None,
        env: Optional[_LiveLocalEnv] = None,
        manifest: Optional[Any] = None,
    ) -> "LocalSessionHandle":
        if env is None:
            env = _LiveLocalEnv(
                manifest or {},
                ProjectionEmitter(InMemoryProjection()),
                tools=tools,
                reasoners=reasoners,
                subs=subs,
                agents=agents,
                planners=planners,
                max_calls=max_calls,
                mode=mode,
                principal=principal,
                event_queue=asyncio.Queue(),
                channel_capacity=channel_capacity,
            )
        return cls(
            session,
            env,
            max_turns=max_turns,
            max_consecutive_turn_errors=max_consecutive_turn_errors,
        )

    async def _drive(self) -> None:
        reason: Optional[str] = None
        turn_body = self._session.body.body
        split_result = bool(
            self._session.body.args and self._session.body.args.get("split") is True
        )
        consecutive_turn_errors = 0
        try:
            if turn_body is None:
                raise ComposableAgentsError("session LOOP missing body")
            for _ in range(self._max_turns):
                try:
                    result = await interpret(turn_body, self._carrier, self._env)
                except SessionClosed:
                    break
                except SessionTurnError as exc:
                    if exc.fatal:
                        raise
                    consecutive_turn_errors += 1
                    if consecutive_turn_errors >= self._max_consecutive_turn_errors:
                        raise
                    await self._events.put(SessionEvent.error(str(exc), fatal=False))
                    if self._env.take_turn_started():
                        await self._events.put(SessionEvent.turn_done())
                    continue
                except Exception as exc:
                    consecutive_turn_errors += 1
                    if consecutive_turn_errors >= self._max_consecutive_turn_errors:
                        raise
                    await self._events.put(SessionEvent.error(str(exc), fatal=False))
                    if self._env.take_turn_started():
                        await self._events.put(SessionEvent.turn_done())
                    continue
                if split_result and isinstance(result.value, tuple) and len(result.value) == 2:
                    self._carrier, output = result.value
                    await self._env.emit(self._session.out_channel, output, result.event_id or "")
                else:
                    self._carrier = result.value
                consecutive_turn_errors = 0
                if self._env.take_turn_started():
                    await self._events.put(SessionEvent.turn_done())
            else:
                raise ComposableAgentsError(
                    f"session consumed more than {self._max_turns} messages"
                )
        except Exception as exc:
            reason = str(exc)
            self._driver_exc = exc
            await self._events.put(SessionEvent.error(reason, fatal=True))
        finally:
            self._closed = True
            self._env.close_channels()
            self._closed_event_sent = True
            await self._events.put(SessionEvent.closed(self._close_reason or reason))
            self._done.set()

    def events(self) -> AsyncIterator[SessionEvent]:
        if self._events_subscribed:
            raise ComposableAgentsError("session events() is single-consumer per handle")
        self._events_subscribed = True

        async def gen() -> AsyncIterator[SessionEvent]:
            while True:
                event = await self._events.get()
                yield event
                if event.is_emit:
                    self._env.evict_emit(event.channel or "", event.seq)
                if event.is_closed:
                    return

        return gen()

    async def send(
        self,
        value: Any,
        *,
        channel: Optional[str] = None,
        idempotency_key: Any = None,
    ) -> dict[str, Any]:
        if self._closed:
            raise SessionClosed("session is closed")
        ch = channel or self._session.in_channel

        if idempotency_key is not None:
            key = str(idempotency_key)
            fingerprint = _local_value_fingerprint(value)
            channel_index = self._idem.setdefault(ch, {})
            prior = channel_index.get(key)
            if prior is not None:
                seq, prior_fingerprint = prior
                if prior_fingerprint != fingerprint:
                    raise ComposableAgentsError(
                        f"idempotency_key {key!r} reused with a different payload "
                        f"on channel {ch!r}"
                    )
                return {"seq": seq, "channel": ch}

        capacity = self._env.capacity()
        if capacity is not None and self._env.pending_count(ch) >= capacity:
            raise ComposableAgentsError(f"ChannelFull: channel {ch!r} is full")

        seq = self._env.append_live(ch, value)
        if idempotency_key is not None:
            self._idem.setdefault(ch, {})[str(idempotency_key)] = (
                seq,
                _local_value_fingerprint(value),
            )
        return {"seq": seq, "channel": ch}

    async def state(self) -> dict[str, Any]:
        return {
            "emitted": self._env.emitted_records(),
            "carrier": self._carrier,
            "closed": self._closed,
            "capacity": self._env.capacity(),
            "pending": self._env.pending_counts(),
        }

    async def open_receives(self) -> list[dict[str, Any]]:
        return self._env.open_receives_records()

    async def close(self, reason: Optional[str] = None) -> None:
        self._close_reason = reason
        self._env.close_channels()
        try:
            await asyncio.gather(self._driver, return_exceptions=True)
        finally:
            if not self._done.is_set():
                self._done.set()
