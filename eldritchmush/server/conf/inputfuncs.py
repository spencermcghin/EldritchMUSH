"""
Input functions

Custom input handlers loaded via settings.INPUT_FUNC_MODULES. Anything
defined here overrides Evennia's defaults of the same name.

We override the `text` handler to write a diagnostic line to
/data/diag.log before forwarding to the stock handler. That gives us
unconditional visibility into every command frame that reaches the
server — which has been impossible to confirm any other way given
Railway's broken log capture.
"""
from evennia.server.inputfuncs import text as _stock_text


def text(session, *args, **kwargs):
    """
    Wrapper around Evennia's stock `text` inputfunc that logs the
    incoming command frame and the session's auth state to the diag
    log, then forwards to the real handler.
    """
    try:
        from web.diag import diag_write

        txt = args[0] if args else None
        diag_write(
            "inputfunc.text RECEIVED",
            sessid=getattr(session, "sessid", None),
            logged_in=getattr(session, "logged_in", None),
            uid=getattr(session, "uid", None),
            account=repr(getattr(session, "account", None)),
            puppet=repr(getattr(session, "puppet", None)),
            text=txt,
        )
    except Exception as exc:
        # Never break command input over a logging issue.
        try:
            from web.diag import diag_write
            diag_write("inputfunc.text DIAG FAILED", exc=str(exc))
        except Exception:
            pass

    # Forward to Evennia's real text handler — same call signature.
    return _stock_text(session, *args, **kwargs)
