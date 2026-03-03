from threading import Lock


class QueryCancelledError(Exception):
    """Raised when a query run has been cancelled by the client."""


_cancelled_sessions: dict[str, bool] = {}
_cancel_lock = Lock()


def request_cancel(session_id: str) -> None:
    if not session_id:
        return
    with _cancel_lock:
        _cancelled_sessions[session_id] = True


def reset_cancel(session_id: str) -> None:
    if not session_id:
        return
    with _cancel_lock:
        _cancelled_sessions.pop(session_id, None)


def is_cancelled(session_id: str | None) -> bool:
    if not session_id:
        return False
    with _cancel_lock:
        return _cancelled_sessions.get(session_id, False)
