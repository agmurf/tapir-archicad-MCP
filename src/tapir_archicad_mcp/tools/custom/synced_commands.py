"""Data-driven sync of add-on commands the bundled toolset is missing or stale on.

The generated tools come from a pinned `multiconn-archicad`, which lags the
installed Tapir add-on (v1.5.2): some commands are absent entirely and several
have stale parameter sets (the generated pydantic models silently strip unknown
fields like beam `width`/`height`). This module reads the add-on's authoritative
schemas (`addon_command_schemas.json`, extracted from the add-on's
command_definitions.js) and registers a passthrough tool for each gap command,
so the CURRENT add-on schema governs and no parameter is lost.

To refresh after an add-on update: re-run schema_sync_audit.py to regenerate
addon_command_schemas.json. No code changes needed — the tools are generated
from the bundle at import time.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.tools.custom.safety import _tapir  # multiconn call w/ reconnect-retry

log = logging.getLogger()

_BUNDLE = Path(__file__).resolve().parents[2] / "addon_command_schemas.json"
_SCHEMAS: Dict[str, Dict[str, Any]] = json.loads(_BUNDLE.read_text(encoding="utf-8")) if _BUNDLE.exists() else {}


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _summarize_params(scheme: Optional[Dict[str, Any]]) -> str:
    if not isinstance(scheme, dict) or not scheme.get("properties"):
        return "Parameters: none (call with an empty object)."
    req = set(scheme.get("required", []))
    lines = []
    for name, d in scheme["properties"].items():
        if not isinstance(d, dict):
            continue
        star = "*" if name in req else ""
        t = d.get("type", "?")
        items = d.get("items")
        if t == "array" and isinstance(items, dict) and items.get("type") == "object":
            ip = items.get("properties", {})
            ir = set(items.get("required", []))
            fields = ", ".join(f"{k}{'*' if k in ir else ''}" for k in ip)
            lines.append(f"  - {name}{star}: array of objects with fields [{fields}]")
        else:
            lines.append(f"  - {name}{star}: {t}")
    return "Parameters (* = required):\n" + "\n".join(lines)


def _register(command: str, meta: Dict[str, Any]) -> None:
    scheme = meta.get("inputScheme")
    desc = (
        (meta.get("description") or "").strip()
        + "\n\n[Synced to the current Tapir add-on — the bundled toolset is missing this "
        "command or omits parameters. Pass the full command parameters as 'parameters'.]\n"
        + _summarize_params(scheme)
    )

    def tool(port: int, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return _tapir(port, command, parameters or {})

    tool.__name__ = "synced_" + _snake(command)
    mcp.tool(name="synced_" + _snake(command), title=command, description=desc)(tool)


_count = 0
for _command, _meta in sorted(_SCHEMAS.items()):
    try:
        _register(_command, _meta)
        _count += 1
    except Exception as e:  # never let one bad entry block server startup
        log.warning("Could not register synced command %s: %s", _command, e)

log.info("Registered %d synced add-on commands (gaps vs the bundled tools).", _count)
