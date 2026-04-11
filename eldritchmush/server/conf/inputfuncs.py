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
    incoming command frame, the session's auth state, AND the full
    cmdset chain visible to the dispatcher, then forwards to the real
    handler.
    """
    try:
        from web.diag import diag_write

        txt = args[0] if args else None

        # Skip keepalive (empty text) frames — they flood the diag log
        # without telling us anything useful.
        if txt is None or (isinstance(txt, str) and not txt.strip()):
            return _stock_text(session, *args, **kwargs)

        diag_write(
            "inputfunc.text RECEIVED",
            sessid=getattr(session, "sessid", None),
            logged_in=getattr(session, "logged_in", None),
            uid=getattr(session, "uid", None),
            account=repr(getattr(session, "account", None)),
            puppet=repr(getattr(session, "puppet", None)),
            text=txt,
        )

        # Dump the cmdset chain for this session — what commands are
        # actually visible to the dispatcher right now. We walk:
        #   1. session.cmdset (session-level commands)
        #   2. account.cmdset (OOC commands when account is logged in)
        #   3. account.cmdset_storage (the persistent string the
        #      cmdset handler reads from on init)
        try:
            session_cmdsets = []
            try:
                if hasattr(session, "cmdset") and session.cmdset:
                    for cs in session.cmdset.all():
                        session_cmdsets.append(getattr(cs, "key", repr(cs)))
            except Exception as exc:
                session_cmdsets = [f"<err: {exc}>"]
            diag_write(
                "  session.cmdset.all()",
                cmdsets=session_cmdsets,
            )

            account = getattr(session, "account", None)
            if account is not None:
                try:
                    acct_cmdsets = []
                    if hasattr(account, "cmdset") and account.cmdset:
                        for cs in account.cmdset.all():
                            acct_cmdsets.append(getattr(cs, "key", repr(cs)))
                    diag_write(
                        "  account.cmdset.all()",
                        cmdsets=acct_cmdsets,
                    )
                except Exception as exc:
                    diag_write("  account.cmdset.all() ERROR", exc=str(exc))
                try:
                    diag_write(
                        "  account.cmdset_storage",
                        storage=account.cmdset_storage,
                        db_cmdset_storage=getattr(account, "db_cmdset_storage", None),
                    )
                except Exception as exc:
                    diag_write("  account.cmdset_storage ERROR", exc=str(exc))

                # Try to find the specific command we care about
                try:
                    found = []
                    if hasattr(account, "cmdset") and account.cmdset:
                        for cs in account.cmdset.all():
                            for cmd in cs.commands:
                                if cmd.key == "charcreate":
                                    found.append(f"{cs.key}:{type(cmd).__module__}.{type(cmd).__name__}")
                    diag_write(
                        "  charcreate lookup",
                        found=found or "NOT FOUND in any account cmdset",
                    )
                except Exception as exc:
                    diag_write("  charcreate lookup ERROR", exc=str(exc))
        except Exception as exc:
            diag_write("inputfunc.text cmdset dump FAILED", exc=str(exc))

    except Exception as exc:
        # Never break command input over a logging issue.
        try:
            from web.diag import diag_write
            diag_write("inputfunc.text DIAG FAILED", exc=str(exc))
        except Exception:
            pass

    # Forward to Evennia's real text handler — same call signature.
    return _stock_text(session, *args, **kwargs)
