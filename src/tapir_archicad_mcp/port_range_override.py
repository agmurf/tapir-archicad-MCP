"""Widen the accepted Archicad JSON-API port range.

Both `multiconn-archicad` (its `Port` type and `MultiConn._port_range`) and the
official `archicad` package (`ACConnection._port_range`) hard-cap the Archicad
JSON port to 19723-19743. Archicad's per-launch JSON port can climb past that
after many restarts (it persists across restarts), which leaves the server
unable to connect even though Archicad is running and a project is open.

Importing this module (done from app.py before MultiConn is built) raises the
upper bound so the server can reach Archicad wherever it bound. This is a
runtime override that lives in our own code — it does not modify the installed
packages and survives `uv sync`. Adjust UPPER if Archicad ever climbs higher.
"""
import logging

import archicad.connection as _ac
import multiconn_archicad.basic_types as _bt
import multiconn_archicad.multi_conn as _mc

log = logging.getLogger()

UPPER = 19774  # accept 19723 .. 19773 inclusive


def _port_new(cls, value):
    if not (19723 <= value < UPPER):
        raise ValueError(f"Port value must be between 19723 and {UPPER}, got {value}.")
    return int.__new__(cls, value)


_bt.Port.__new__ = _port_new
_mc.MultiConn._port_range = [_bt.Port(p) for p in range(19723, UPPER)]
_ac.ACConnection._port_range = staticmethod(lambda: range(19723, UPPER, 1))

log.info("Archicad JSON port range widened to 19723-%d", UPPER - 1)
