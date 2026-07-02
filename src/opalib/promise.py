"""promise - Promise-like continuation helper ported from promise.lua."""

import threading
import traceback
import warnings
from typing import Any, Callable, Dict, List, Optional


def _get_trace(err: BaseException) -> str:
    return traceback.format_exc()


class OP:
    NONE = object()
    CONTINUE = object()
    THROW = object()
    REPEAT = object()
    RESUME = object()


dispatch: Optional[Callable[[Any], Any]] = None


def set_dispatch(fn: Callable[[Any], Any]) -> None:
    global dispatch
    dispatch = fn


def _spawn(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> threading.Thread:
    thread = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


class Promise:
    """A continuation-style promise container."""

    def __init__(self, state: Optional[Dict[str, Any]] = None, *callbacks: Callable[["Promise", Any], Any]) -> None:
        object.__setattr__(self, "i", 1)
        object.__setattr__(self, "state", state or {})
        object.__setattr__(self, "is_running", False)
        object.__setattr__(self, "after", OP.NONE)
        object.__setattr__(self, "after_args", None)
        object.__setattr__(self, "caller", None)
        object.__setattr__(self, "predecessor", None)
        object.__setattr__(self, "on_error", None)
        object.__setattr__(self, "silent", False)
        object.__setattr__(self, "msg", None)
        object.__setattr__(self, "_actions", list(callbacks))

    def __getattr__(self, name: str) -> Any:
        state = object.__getattribute__(self, "state")
        if name in state:
            return state[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {
            "i",
            "state",
            "is_running",
            "after",
            "after_args",
            "caller",
            "predecessor",
            "on_error",
            "silent",
            "msg",
            "_actions",
        }:
            object.__setattr__(self, name, value)
        else:
            self.state[name] = value

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if kwargs:
            raise TypeError("Promise call only accepts positional arguments")
        arg = args[0] if len(args) == 1 else args
        return self.continue(arg)

    def then(self, callback: Callable[["Promise", Any], Any]) -> "Promise":
        self._actions.append(callback)
        return self

    def else(self, callback: Callable[["Promise", Any], Any]) -> "Promise":
        return self.on_error().then(callback)

    def on_error(self) -> "Promise":
        on_error = object.__getattribute__(self, "on_error")
        if on_error is None:
            on_error = Promise(self.state)
            object.__setattr__(self, "on_error", on_error)
            object.__setattr__(on_error, "predecessor", self)
        return on_error

    def silent(self) -> "Promise":
        object.__setattr__(self, "silent", True)
        return self

    def _Dispatch(self, op: object, arg: Any = None, msg: Any = None) -> Any:
        if msg is not None:
            object.__setattr__(self, "msg", msg)

        if object.__getattribute__(self, "is_running"):
            object.__setattr__(self, "after", op)
            object.__setattr__(self, "after_args", arg)
            return None

        if op is OP.RESUME:
            op = object.__getattribute__(self, "after")
            old_args = object.__getattribute__(self, "after_args")
            if old_args is not None:
                arg = old_args

        while op is not OP.NONE:
            object.__setattr__(self, "after", OP.CONTINUE)
            object.__setattr__(self, "after_args", None)

            if op is OP.THROW:
                on_error = object.__getattribute__(self, "on_error")
                if on_error is None:
                    print("An unhandled error occured.")
                if not object.__getattribute__(self, "silent") and isinstance(self.msg, str):
                    warnings.warn(self.msg)
                if on_error is not None:
                    return on_error._Dispatch(OP.CONTINUE, arg, msg)

            index = object.__getattribute__(self, "i")
            if op is OP.REPEAT:
                index -= 1
            else:
                object.__setattr__(self, "i", index + 1)

            actions = object.__getattribute__(self, "_actions")
            action = actions[index - 1] if 0 <= index - 1 < len(actions) else None

            if action is not None:
                if callable(action):
                    object.__setattr__(self, "is_running", True)
                    try:
                        value = action(self, arg)
                    except Exception as err:
                        value = _get_trace(err)
                        object.__setattr__(self, "after", OP.THROW)
                        object.__setattr__(self, "after_args", arg)
                        msg = value
                        object.__setattr__(self, "msg", msg)
                    finally:
                        object.__setattr__(self, "is_running", False)

                    if isinstance(value, Promise):
                        object.__setattr__(value, "caller", self)
                        return value._Dispatch(OP.CONTINUE)
                else:
                    action_type = None
                    if isinstance(action, dict):
                        action_type = action.get("type")
                    else:
                        action_type = getattr(action, "type", None)
                    if action_type is None:
                        raise TypeError("Table is not an action to be dispatched")
                    if dispatch is None:
                        raise RuntimeError("No dispatch function defined")
                    dispatch(action)
            else:
                object.__setattr__(self, "i", 1)
                object.__setattr__(self, "after", OP.NONE)
                predecessor = object.__getattribute__(self, "predecessor")
                if predecessor is not None:
                    caller = object.__getattribute__(predecessor, "caller")
                    if caller is not None:
                        caller.throw_async(arg, msg=self.msg)
                caller = object.__getattribute__(self, "caller")
                if caller is not None:
                    caller.resume_async(arg)
                return arg

            op = object.__getattribute__(self, "after")
            arg = object.__getattribute__(self, "after_args")

        return arg

    def return_async(self, arg: Any = None) -> threading.Thread:
        caller = object.__getattribute__(self, "caller")
        if caller is None:
            raise RuntimeError("No caller available for ReturnAsync")
        return caller.resume_async(arg)

    def escalate_async(self, arg: Any = None) -> threading.Thread:
        predecessor = object.__getattribute__(self, "predecessor")
        if predecessor is None:
            raise RuntimeError("No predecessor available for EscalateAsync")
        caller = object.__getattribute__(predecessor, "caller")
        if caller is None:
            raise RuntimeError("No caller available for EscalateAsync")
        return caller.throw_async(arg, msg=self.msg)

    def continue(self, arg: Any = None) -> Any:
        return self._Dispatch(OP.CONTINUE, arg)

    def yield(self) -> None:
        object.__setattr__(self, "after", OP.NONE)

    def continue_async(self, arg: Any = None) -> threading.Thread:
        return _spawn(self._Dispatch, OP.CONTINUE, arg)

    def throw(self, arg: Any = None, msg: Any = None) -> Any:
        return self._Dispatch(OP.THROW, arg, msg=msg)

    def throw_async(self, arg: Any = None, msg: Any = None) -> threading.Thread:
        return _spawn(self._Dispatch, OP.THROW, arg, msg=msg)

    def repeat(self, arg: Any = None) -> Any:
        return self._Dispatch(OP.REPEAT, arg)

    def repeat_async(self, arg: Any = None) -> threading.Thread:
        return _spawn(self._Dispatch, OP.REPEAT, arg)

    def resume(self, arg: Any = None) -> Any:
        return self._Dispatch(OP.RESUME, arg)

    def resume_async(self, arg: Any = None) -> threading.Thread:
        return _spawn(self._Dispatch, OP.RESUME, arg)

    def reset(self) -> None:
        object.__setattr__(self, "i", 1)

    def stop(self) -> None:
        self.Yield()
        self.Reset()

    def retry_async(self, arg: Any = None) -> threading.Thread:
        predecessor = object.__getattribute__(self, "predecessor")
        if predecessor is None:
            raise RuntimeError("No predecessor available for RetryAsync")
        predecessor.Reset()
        return predecessor.continue_async(arg)


__all__ = ["Promise", "OP", "dispatch", "set_dispatch"]
