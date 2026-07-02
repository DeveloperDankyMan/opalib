"""
opalib.http — Promise-based HTTP request helper.

Updated to match the improved Promise implementation:
- Thread-safe
- No attribute collisions
- Uses Promise.then(), Promise.else_(), Promise.silent()
- Uses Promise.continue_(), Promise.throw(), Promise.repeat(), etc.
"""

import threading
import time
import traceback
import warnings
from typing import Any, Dict, Optional, Union
from urllib.error import HTTPError
from urllib.request import Request as UrlRequest, urlopen

from opalib.promise import Promise, OP

TIMEOUT = 120.0
ERR_TIMED_OUT = "Request timed out at %d seconds."
ERR_LATE = "Response arrived late (after %d seconds)."
ERR_HTTP = 'Request received HTTP %d %s "%s"'
ERR_RBX = 'Request received an error: "%s"'


# ------------------------------------------------------------
# Linked list node for timeout watcher
# ------------------------------------------------------------

class _LinkNode:
    pass


LL = _LinkNode()
LL.prev = LL
LL.next = LL


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _normalize_arg(args: Dict[str, Any], primary: str, fallback: str) -> Any:
    return args.get(primary, args.get(fallback))


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


# ------------------------------------------------------------
# Request object
# ------------------------------------------------------------

class Request:
    def __init__(self, args: Dict[str, Any]) -> None:
        self.promise: Optional[Promise] = None
        self.success: Optional[bool] = None
        self.response: Any = None
        self.args = args

        # Linked list pointers
        self.next: Optional[Request] = None
        self.prev: Optional[Request] = None

        # Timing
        self.start_t = float("inf")
        self.finish_t = float("inf")
        self.is_active = True

        # Debug
        self.traceback = "".join(traceback.format_stack()[:-1])
        self.msg: Optional[str] = None

    # ------------------------------------------------------------
    # HTTP request execution
    # ------------------------------------------------------------

    def _send_request(self) -> Dict[str, Any]:
        url = _normalize_arg(self.args, "Url", "url")
        if not url:
            raise ValueError("Missing Url")

        method = _normalize_arg(self.args, "Method", "method") or "GET"
        headers = _normalize_arg(self.args, "Headers", "headers") or {}
        data = _normalize_arg(self.args, "Body", "body")

        if data is None:
            request_data = None
        elif isinstance(data, bytes):
            request_data = data
        elif isinstance(data, str):
            request_data = data.encode("utf-8")
        else:
            request_data = str(data).encode("utf-8")

        req = UrlRequest(url, data=request_data, headers=headers, method=method)

        try:
            with urlopen(req, timeout=TIMEOUT) as response:
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

    # ------------------------------------------------------------
    # Error handler
    # ------------------------------------------------------------

    def default_throw(self, promise: Promise, arg: Any) -> Any:
        if not self.is_active:
            flight_time = self.finish_t - self.start_t
            if self.success is None:
                warnings.warn(ERR_TIMED_OUT % flight_time)
            else:
                warnings.warn(ERR_LATE % flight_time)

        response = self.response

        # HTTP success but logical failure
        if self.success is True and isinstance(response, dict):
            if response.get("Success"):
                warnings.warn(self.msg or "Request completed with an unexpected error.")

            elif response.get("StatusCode") == 401 and response.get("Body") == "Session has expired":
                refresh_callback = self.args.get("refresh")

                if callable(refresh_callback) and promise._predecessor is not None:
                    try:
                        refresh_data = refresh_callback(self.args)
                        if isinstance(refresh_data, dict):
                            self.args.update(refresh_data.get("args", {}))
                            self.args["Headers"] = {
                                **self.args.get("Headers", {}),
                                **refresh_data.get("headers", {}),
                            }

                        promise.stop()
                        return promise._predecessor.repeat_async()

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
        return promise.continue_(arg)

    # ------------------------------------------------------------
    # Main execution callback
    # ------------------------------------------------------------

    def exec(self, promise: Promise, arg: Any) -> Any:
        # Insert into linked list
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

        # Remove from active list
        if self.is_active:
            self.prev.next = self.next
            self.next.prev = self.prev

        # Late response handling
        elif not _normalize_arg(self.args, "AcceptLate", "accept_late"):
            return promise.throw(self.response, msg=self.msg)

        # Success path
        if self.success is True and isinstance(self.response, dict) and self.response.get("Success"):
            return promise.continue_(self.response)

        # Failure path
        return promise.throw(self.response, msg=self.msg)


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def req(args: Dict[str, Any]) -> Promise:
    request = Request(args)
    promise = Promise({"request": request})

    request.promise = promise

    promise.silent().then(request.exec).else_(request.default_throw)

    threading.Timer(0, promise.continue_async).start()
    return promise


# ------------------------------------------------------------
# Timeout watcher thread
# ------------------------------------------------------------

def _timeout_watcher() -> None:
    while True:
        now = time.time()
        current = LL.next

        while current is not LL and current.is_active and now - current.start_t > TIMEOUT:
            current.is_active = False
            current.promise.throw_async()
            current = current.next

        LL.next = current
        current.prev = LL

        time.sleep(0.1)


threading.Thread(target=_timeout_watcher, daemon=True).start()


__all__ = ["req"]
