"""
promise.py — A continuation‑style Promise system inspired by promise.lua,
rewritten for Python with thread‑safety, clearer semantics, and safer dispatch.
"""

import threading
import traceback
import warnings
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


# ------------------------------------------------------------
# Operation Enum
# ------------------------------------------------------------

class OP(Enum):
    NONE = auto()
    CONTINUE = auto()
    THROW = auto()
    REPEAT = auto()
    RESUME = auto()


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _trace(err: BaseException) -> str:
    return traceback.format_exc()


def _spawn(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> threading.Thread:
    thread = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=False)
    thread.start()
    return thread


# ------------------------------------------------------------
# Promise Class
# ------------------------------------------------------------

class Promise:
    """
    A continuation‑style Promise container with safe chaining,
    thread‑safe state, and explicit dispatch.
    """

    def __init__(
        self,
        state: Optional[Dict[str, Any]] = None,
        *callbacks: Callable[["Promise", Any], Any],
        dispatch: Optional[Callable[[Any], Any]] = None,
    ) -> None:

        # Internal state
        self._i = 1
        self._state = state or {}
        self._actions: List[Any] = list(callbacks)
        self._dispatch_fn = dispatch

        # Execution state
        self._is_running = False
        self._after = OP.NONE
        self._after_args = None
        self._caller: Optional["Promise"] = None
        self._predecessor: Optional["Promise"] = None
        self._on_error: Optional["Promise"] = None
        self._silent = False
        self._msg: Optional[Any] = None

        # Thread safety
        self._lock = threading.RLock()

    # ------------------------------------------------------------
    # Attribute access
    # ------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        if name in self._state:
            return self._state[name]
        raise AttributeError(f"Promise has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        # Internal attributes
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            # User state
            self._state[name] = value

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def __call__(self, *args: Any) -> Any:
        arg = args[0] if len(args) == 1 else args
        return self.continue_(arg)

    def then(self, callback: Callable[["Promise", Any], Any]) -> "Promise":
        self._actions.append(callback)
        return self

    def else_(self, callback: Callable[["Promise", Any], Any]) -> "Promise":
        return self.on_error().then(callback)

    def on_error(self) -> "Promise":
        if self._on_error is None:
            self._on_error = Promise(self._state, dispatch=self._dispatch_fn)
            self._on_error._predecessor = self
        return self._on_error

    def silent(self) -> "Promise":
        self._silent = True
        return self

    # ------------------------------------------------------------
    # Core dispatch
    # ------------------------------------------------------------

    def _dispatch(self, op: OP, arg: Any = None, msg: Any = None) -> Any:
        with self._lock:
            if msg is not None:
                self._msg = msg

            # If already running, queue the operation
            if self._is_running:
                self._after = op
                self._after_args = arg
                return None

            # Resume means: use queued op
            if op is OP.RESUME:
                op = self._after
                if self._after_args is not None:
                    arg = self._after_args

            while op is not OP.NONE:
                self._after = OP.CONTINUE
                self._after_args = None

                # Error handling
                if op is OP.THROW:
                    if self._on_error is None:
                        warnings.warn("Unhandled Promise error")
                    if not self._silent and isinstance(self._msg, str):
                        warnings.warn(self._msg)
                    if self._on_error is not None:
                        return self._on_error._dispatch(OP.CONTINUE, arg, msg)

                # Determine next action
                index = self._i
                if op is OP.REPEAT:
                    index -= 1
                else:
                    self._i = index + 1

                action = self._actions[index - 1] if 0 <= index - 1 < len(self._actions) else None

                # Execute action
                if action is not None:
                    if callable(action):
                        self._is_running = True
                        try:
                            value = action(self, arg)
                        except Exception as err:
                            self._after = OP.THROW
                            self._after_args = arg
                            self._msg = _trace(err)
                            value = None
                        finally:
                            self._is_running = False

                        # Promise chaining
                        if isinstance(value, Promise):
                            value._caller = self
                            return value._dispatch(OP.CONTINUE)

                    else:
                        # Table‑style action
                        action_type = getattr(action, "type", None)
                        if action_type is None:
                            raise TypeError("Invalid action object")

                        if self._dispatch_fn is None:
                            raise RuntimeError("No dispatch function defined")

                        self._dispatch_fn(action)

                else:
                    # End of chain
                    self._i = 1
                    self._after = OP.NONE

                    # Escalate to predecessor
                    if self._predecessor is not None:
                        caller = self._predecessor._caller
                        if caller is not None:
                            caller.throw_async(arg, msg=self._msg)

                    # Resume caller
                    if self._caller is not None:
                        self._caller.resume_async(arg)

                    return arg

                op = self._after
                arg = self._after_args

            return arg

    # ------------------------------------------------------------
    # Public continuation methods
    # ------------------------------------------------------------

    def continue_(self, arg: Any = None) -> Any:
        return self._dispatch(OP.CONTINUE, arg)

    def continue_async(self, arg: Any = None) -> threading.Thread:
        return _spawn(self._dispatch, OP.CONTINUE, arg)

    def throw(self, arg: Any = None, msg: Any = None) -> Any:
        return self._dispatch(OP.THROW, arg, msg)

    def throw_async(self, arg: Any = None, msg: Any = None) -> threading.Thread:
        return _spawn(self._dispatch, OP.THROW, arg, msg)

    def repeat(self, arg: Any = None) -> Any:
        return self._dispatch(OP.REPEAT, arg)

    def repeat_async(self, arg: Any = None) -> threading.Thread:
        return _spawn(self._dispatch, OP.REPEAT, arg)

    def resume(self, arg: Any = None) -> Any:
        return self._dispatch(OP.RESUME, arg)

    def resume_async(self, arg: Any = None) -> threading.Thread:
        return _spawn(self._dispatch, OP.RESUME, arg)

    def return_async(self, arg: Any = None) -> threading.Thread:
        if self._caller is None:
            raise RuntimeError("No caller available for return_async")
        return self._caller.resume_async(arg)

    def escalate_async(self, arg: Any = None) -> threading.Thread:
        if self._predecessor is None:
            raise RuntimeError("No predecessor available for escalate_async")
        caller = self._predecessor._caller
        if caller is None:
            raise RuntimeError("No caller available for escalate_async")
        return caller.throw_async(arg, msg=self._msg)

    def retry_async(self, arg: Any = None) -> threading.Thread:
        if self._predecessor is None:
            raise RuntimeError("No predecessor available for retry_async")
        self._predecessor._i = 1
        return self._predecessor.continue_async(arg)

    # ------------------------------------------------------------
    # Reset / Stop
    # ------------------------------------------------------------

    def reset(self) -> None:
        self._i = 1

    def stop(self) -> None:
        self._after = OP.NONE
        self.reset()


__all__ = ["Promise", "OP"]
