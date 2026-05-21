"""http - Promise-based HTTP request helper for opalib.

This module is a Python port of the Roblox/ Lua `http.lua` helper.
It exposes a single `req` function that returns a `Promise` and
provides request timeout handling, late response detection, and
basic response shaping compatible with the Lua implementation.
"""

import threading
import time
import traceback
import warnings
from typing import Any, Callable, Dict, Optional, Union
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen

from src.promise import Promise

TIMEOUT = 120.0
ERR_TIMED_OUT = "Request timed out at %d seconds."
ERR_LATE = "Response arrived late (after %d seconds)."
ERR_HTTP = 'Request received HTTP %d %s "%s"'
ERR_RBX = 'Request received an error: "%s"'


class _LinkNode:
    pass


LL = _LinkNode()
LL.prev = LL
LL.next = LL


def _normalize_arg(args: Dict[str, Any], primary: str, fallback: str) -> Any:
    if primary in args:
        return args[primary]
    return args.get(fallback)


def _make_response(success: bool, status: int, message: str, body: Union[str, bytes]) -> Dict[str, Any]:
    if isinstance(body, bytes):
        try:
            body_text = body.decode("utf-8")
        except Exception:
            body_text = body
    else:
        body_text = body

    return {
        "Success": success,
        "StatusCode": status,
        "StatusMessage": message,
        "Body": body_text,
    }


class Request:
    def __init__(self, args: Dict[str, Any]) -> None:
        self.promise: Optional[Promise] = None
        self.success: Optional[bool] = None
        self.response: Any = None
        self.args = args
        self.next: Optional[Request] = None
        self.prev: Optional[Request] = None
        self.start_t = float("inf")
        self.finish_t = float("inf")
        self.is_active = True
        self.traceback = "".join(traceback.format_stack()[:-1])
        self.msg: Optional[str] = None

    def _send_request(self) -> Dict[str, Any]:
        url = _normalize_arg(self.args, "Url", "url")
        if not url:
            raise ValueError("Missing Url")

        method = _normalize_arg(self.args, "Method", "method") or "GET"
        headers = _normalize_arg(self.args, "Headers", "headers") or {}
        data = _normalize_arg(self.args, "Body", "body")

        request_data: Optional[bytes]
        if data is None:
            request_data = None
        elif isinstance(data, bytes):
            request_data = data
        elif isinstance(data, str):
            request_data = data.encode("utf-8")
        else:
            request_data = str(data).encode("utf-8")

        request = UrlRequest(url, data=request_data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=TIMEOUT) as response:
                body = response.read()
                return _make_response(
                    200 <= response.status < 400,
                    response.status,
                    response.reason or "",
                    body,
                )
        except HTTPError as err:
            body = err.read()
            return _make_response(
                False,
                err.code,
                err.reason or "",
                body,
            )

    def default_throw(self, promise: Promise, arg: Any) -> Any:
        if not self.is_active:
            flight_time = self.finish_t - self.start_t
            if self.success is None:
                warnings.warn(ERR_TIMED_OUT % flight_time)
            else:
                warnings.warn(ERR_LATE % flight_time)

        response = self.response
        if self.success is True and isinstance(response, dict):
            if response.get("Success"):
                warnings.warn(self.msg or "Request completed with an unexpected error.")
            elif response.get("StatusCode") == 401 and response.get("Body") == "Session has expired":
                refresh_callback = self.args.get("refresh")
                if callable(refresh_callback) and promise.predecessor is not None:
                    try:
                        refresh_data = refresh_callback(self.args)
                        if isinstance(refresh_data, dict):
                            self.args.update(refresh_data.get("args", {}))
                            self.args["Headers"] = {
                                **self.args.get("Headers", {}),
                                **refresh_data.get("headers", {}),
                            }
                        promise.Stop()
                        return promise.predecessor.RepeatAsync()
                    except Exception as err:
                        warnings.warn(f"Refresh callback failed: {err}")
                warnings.warn(ERR_HTTP % (response["StatusCode"], response["StatusMessage"], response["Body"]))
            else:
                warnings.warn(ERR_HTTP % (response["StatusCode"], response["StatusMessage"], response["Body"]))
        elif self.success is False:
            warnings.warn(ERR_RBX % response)
        else:
            warnings.warn(self.msg or "Request failed before sending.")

        print(self.traceback)
        return promise.Continue(arg)

    def exec(self, promise: Promise, arg: Any) -> Any:
        self.next = LL
        self.prev = LL.prev
        self.next.prev = self
        self.prev.next = self

        self.start_t = time.time()
        try:
            self.success = True
            self.response = self._send_request()
        except Exception as err:
            self.success = False
            self.response = str(err)
            self.msg = str(err)
        finally:
            self.finish_t = time.time()

        if self.is_active:
            self.prev.next = self.next
            self.next.prev = self.prev
        elif not _normalize_arg(self.args, "AcceptLate", "accept_late"):
            return promise.Throw(self.response, msg=self.msg)

        if self.success is True and isinstance(self.response, dict) and self.response.get("Success"):
            return promise.Continue(self.response)

        return promise.Throw(self.response, msg=self.msg)


def req(args: Dict[str, Any]) -> Promise:
    request = Request(args)
    request.promise = Promise({"request": request})
    request.promise.Silent().Then(request.exec).Else(request.default_throw)
    threading.Timer(0, request.promise.ContinueAsync).start()
    return request.promise


def _timeout_watcher() -> None:
    while True:
        now = time.time()
        current = LL.next
        while current is not LL and current.is_active and now - current.start_t > TIMEOUT:
            current.is_active = False
            current.promise.ThrowAsync()
            current = current.next

        LL.next = current
        current.prev = LL
        time.sleep(0.1)


threading.Thread(target=_timeout_watcher, daemon=True).start()


__all__ = ["req"]
