"""Safety / agentic-write-path tools (Architech, spec section 7).

These complement the generated Create* tools with the safeguards a live-BIM
write path needs: geometry validation BEFORE create, read-back verification of
what was created, and selection of a session's elements for human review / bulk
removal. All Archicad access goes through the same multiconn connection the
generated tools use (Tapir commands via post_tapir_command).
"""
import logging
import math
from typing import Any, Dict, List

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.context import multi_conn_instance
from multiconn_archicad.basic_types import Port

log = logging.getLogger()

EXTENT = 1.0e5  # metres; coordinates beyond this are almost certainly a mistake


# --------------------------------------------------------------------------- connection helper
# A long-lived server's connection to Archicad can intermittently hang on a stale /
# unresponsive socket. Without a timeout that blocks for minutes (Claude Desktop then
# reports the tool as "timed out"). We bound every call with a timeout so a stuck call
# fails in seconds, and on failure we refresh the connection so the NEXT call is healthy.
# We deliberately do NOT auto-re-run the command: a create may have partially executed,
# and a blind retry would duplicate it. The caller can retry on the now-fresh connection.
_CALL_TIMEOUT = 45.0  # seconds; generous for legitimate ops, far below a 4-min hang


def _tapir(port: int, command: str, params: Dict[str, Any] | None = None,
           timeout: float = _CALL_TIMEOUT) -> Dict[str, Any]:
    multi_conn = multi_conn_instance.get()
    tp = Port(port)
    if tp not in multi_conn.active:
        # connection list may be stale (e.g. Archicad was reopened) - refresh once
        try:
            multi_conn.refresh.all_ports()
            multi_conn.connect.all()
        except Exception:
            pass
    if tp not in multi_conn.active:
        raise ValueError(f"Port {port} is not an active Archicad connection.")
    try:
        return multi_conn.active[tp].core.post_tapir_command(
            command=command, parameters=params or {}, timeout=timeout)
    except Exception as e:
        log.warning("post_tapir_command(%s) failed/timed out (%s); refreshing connection for next call.",
                    command, type(e).__name__)
        try:
            multi_conn.refresh.all_ports()
            multi_conn.connect.all()
        except Exception:
            pass
        raise


# --------------------------------------------------------------------------- geometry validation
def _finite(*vals) -> bool:
    return all(isinstance(v, (int, float)) and math.isfinite(v) for v in vals)


def _coord_ok(c, errs, where) -> bool:
    if not isinstance(c, dict) or not _finite(c.get("x"), c.get("y")):
        errs.append(f"{where}: coordinate missing or non-finite ({c})")
        return False
    if abs(c["x"]) > EXTENT or abs(c["y"]) > EXTENT:
        errs.append(f"{where}: coordinate out of plausible extent ({c['x']},{c['y']})")
        return False
    return True


def _dist(a, b) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def _segments_intersect(p1, p2, p3, p4) -> bool:
    def ccw(a, b, c):
        return (c["y"] - a["y"]) * (b["x"] - a["x"]) - (b["y"] - a["y"]) * (c["x"] - a["x"])
    d1, d2 = ccw(p3, p4, p1), ccw(p3, p4, p2)
    d3, d4 = ccw(p1, p2, p3), ccw(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _poly_self_intersects(pts) -> bool:
    n = len(pts)
    edges = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if abs(i - j) <= 1 or (i == 0 and j == n - 1):
                continue
            if _segments_intersect(*edges[i], *edges[j]):
                return True
    return False


def _poly_area(pts) -> float:
    s = 0.0
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        s += a["x"] * b["y"] - b["x"] * a["y"]
    return abs(s) / 2.0


def _validate_walls(walls) -> List[str]:
    errs: List[str] = []
    for i, w in enumerate(walls):
        b, e = w.get("begCoordinate"), w.get("endCoordinate")
        ok = _coord_ok(b, errs, f"wall[{i}].begCoordinate") & _coord_ok(e, errs, f"wall[{i}].endCoordinate")
        if ok and _dist(b, e) < 1e-3:
            errs.append(f"wall[{i}]: zero-length wall")
        for k in ("height", "thickness"):
            v = w.get(k)
            if v is not None and (not _finite(v) or v <= 0):
                errs.append(f"wall[{i}].{k} must be positive ({v})")
    return errs


def _validate_polygon(coords, where, min_pts=3) -> List[str]:
    errs: List[str] = []
    if not isinstance(coords, list) or len(coords) < min_pts:
        errs.append(f"{where}: polygon needs >= {min_pts} coordinates")
        return errs
    clean = [c for j, c in enumerate(coords) if _coord_ok(c, errs, f"{where}[{j}]")]
    if len(clean) < min_pts:
        return errs
    if _poly_area(clean) < 1e-6:
        errs.append(f"{where}: degenerate polygon (area ~ 0)")
    if _poly_self_intersects(clean):
        errs.append(f"{where}: self-intersecting polygon")
    return errs


def _validate_openings(items, key) -> List[str]:
    errs: List[str] = []
    for i, o in enumerate(items):
        owner = o.get(key)
        if not (isinstance(owner, dict) and owner.get("guid")):
            errs.append(f"opening[{i}]: missing/invalid owner '{key}'")
        w = o.get("width")
        if w is not None and (not _finite(w) or w <= 0):
            errs.append(f"opening[{i}].width must be positive ({w})")
    return errs


def _validate_payload(command: str, payload: Dict[str, Any]) -> List[str]:
    if command == "CreateWalls":
        return _validate_walls(payload.get("wallsData", []))
    if command in ("CreateSlabs", "CreateRoofs"):
        field = "slabsData" if command == "CreateSlabs" else "roofsData"
        errs: List[str] = []
        for i, item in enumerate(payload.get(field, [])):
            errs += _validate_polygon(item.get("polygonCoordinates", []), f"{command}[{i}].polygonCoordinates")
        return errs
    if command == "CreateZones":
        errs = []
        for i, item in enumerate(payload.get("zonesData", [])):
            errs += _validate_polygon(item.get("geometry", {}).get("polygonCoordinates", []), f"zone[{i}]")
        return errs
    if command in ("CreateDoors", "CreateWindows"):
        field = "doorsData" if command == "CreateDoors" else "windowsData"
        return _validate_openings(payload.get(field, []), "ownerWallId")
    if command == "CreateOpenings":
        return _validate_openings(payload.get("openingsData", []), "ownerElementId")
    return []


# Generated create-tool name -> Tapir command, for always-on validation in the
# dispatcher (archicad_call_tool). Only commands that have a geometry validator
# are listed; everything else passes through unchanged.
_VALIDATED_TOOLS = {
    "elements_create_walls": "CreateWalls",
    "elements_create_slabs": "CreateSlabs",
    "elements_create_roofs": "CreateRoofs",
    "elements_create_zones": "CreateZones",
    "elements_create_doors": "CreateDoors",
    "elements_create_windows": "CreateWindows",
    "elements_create_openings": "CreateOpenings",
}


def validate_tool_call(tool_name: str, params: Any) -> List[str]:
    """Always-on geometry validation hook for the dispatcher. Returns [] for tools
    without a validator; otherwise the list of validation errors for `params`."""
    command = _VALIDATED_TOOLS.get(tool_name)
    if not command or not isinstance(params, dict):
        return []
    try:
        return _validate_payload(command, params)
    except Exception as e:  # never let the validator itself break a call
        log.warning("validate_tool_call(%s) errored: %s", tool_name, e)
        return []


def _bbox_union(boxes):
    fs = [b for b in boxes if b]
    if not fs:
        return None
    return {
        "xMin": min(b["xMin"] for b in fs), "xMax": max(b["xMax"] for b in fs),
        "yMin": min(b["yMin"] for b in fs), "yMax": max(b["yMax"] for b in fs),
        "zMin": min(b["zMin"] for b in fs), "zMax": max(b["zMax"] for b in fs),
    }


def _iter_xy(payload):
    def walk(o):
        if isinstance(o, dict):
            if "x" in o and "y" in o and _finite(o.get("x"), o.get("y")):
                z = o.get("z", 0.0)
                yield (o["x"], o["y"], z if _finite(z) else 0.0)
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    yield from walk(payload)


def _preview(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    field = next((k for k in payload if k.endswith("Data")), None)
    items = payload.get(field, []) if field else []
    errs = _validate_payload(command, payload)
    pts = list(_iter_xy(payload))
    bbox = None
    if pts:
        bbox = {"xMin": min(p[0] for p in pts), "xMax": max(p[0] for p in pts),
                "yMin": min(p[1] for p in pts), "yMax": max(p[1] for p in pts),
                "zMin": min(p[2] for p in pts), "zMax": max(p[2] for p in pts)}
    return {
        "command": command, "dryRun": True, "wouldCreate": len(items),
        "valid": not errs, "validationErrors": errs, "approxBoundingBox": bbox,
        "note": "Nothing was created. Bounding box derived from input coordinates "
                "(excludes thickness/height extrusion).",
    }


def _verify(port: int, guids: List[str]) -> Dict[str, Any]:
    elements = [{"elementId": {"guid": g}} for g in guids]
    details = _tapir(port, "GetDetailsOfElements", {"elements": elements}) or {}
    bb = _tapir(port, "Get3DBoundingBoxes", {"elements": elements}) or {}
    by_type: Dict[str, int] = {}
    per = []
    for d in details.get("detailsOfElements", []):
        if "error" in d:
            continue
        t = d.get("type", "?")
        by_type[t] = by_type.get(t, 0) + 1
        per.append({"type": t, "layerIndex": d.get("layerIndex"), "id": d.get("id")})
    boxes = [b.get("boundingBox3D") for b in bb.get("boundingBoxes3D", []) if isinstance(b, dict)]
    return {
        "requested": len(guids), "verified": len(per), "missing": len(guids) - len(per),
        "byType": by_type, "combinedBoundingBox": _bbox_union(boxes), "elements": per,
    }


# --------------------------------------------------------------------------- MCP tools
@mcp.tool(
    name="safety_validate_geometry",
    title="Validate Create Geometry",
    description=(
        "Validate a Create command payload BEFORE sending it to Archicad. Rejects zero-length walls, "
        "degenerate or self-intersecting polygons, non-finite/out-of-extent coordinates, and openings "
        "with missing owners. Returns {valid, errors}. Call this before any Create* tool on non-trivial geometry."
    ),
)
def validate_geometry(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    errs = _validate_payload(command, payload)
    return {"valid": not errs, "errors": errs}


@mcp.tool(
    name="safety_verify_created_elements",
    title="Verify Created Elements (read-back)",
    description=(
        "Read-back verification for a set of element GUIDs (e.g. the GUIDs returned by Create* tools). "
        "Returns a confirmation summary: how many were found, a per-type tally, and the combined 3D "
        "bounding box. Use after a create batch to confirm what actually landed in the model."
    ),
)
def verify_created_elements(port: int, element_guids: List[str]) -> Dict[str, Any]:
    return _verify(port, element_guids)


@mcp.tool(
    name="safety_select_elements",
    title="Select Elements in Archicad",
    description=(
        "Select the given element GUIDs in Archicad so a human can review them (and delete them with the "
        "delete tool if unwanted). Useful for auditing everything an AI session created."
    ),
)
def select_elements(port: int, element_guids: List[str]) -> Dict[str, Any]:
    elements = [{"elementId": {"guid": g}} for g in element_guids]
    return _tapir(port, "ChangeSelectionOfElements", {"addElementsToSelection": elements})


@mcp.tool(
    name="safety_preview_create",
    title="Preview Create (dry run)",
    description=(
        "Dry run for a Create command: validates the payload and reports what WOULD be created "
        "(item count + an approximate bounding box derived from the input coordinates) without "
        "committing anything to the model. Use to preview before a large/non-trivial create."
    ),
)
def preview_create(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _preview(command, payload)


@mcp.tool(
    name="safety_safe_create",
    title="Safe Create (validate -> create -> verify)",
    description=(
        "The safe agentic write path. Validates the payload; if invalid, returns the errors and creates "
        "NOTHING. If valid, runs the given Create command, then reads back and verifies the result. "
        "command is a Tapir create command name (e.g. 'CreateWalls', 'CreateSlabs'); payload is that "
        "command's parameters object. Set select=true to also select the created elements; set "
        "dry_run=true to only preview (count + bounding box) and create nothing."
    ),
)
def safe_create(port: int, command: str, payload: Dict[str, Any], select: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run:
        return _preview(command, payload)
    report: Dict[str, Any] = {"command": command, "committed": False}
    errs = _validate_payload(command, payload)
    if errs:
        report["validationErrors"] = errs
        report["message"] = "Rejected before create — fix geometry and retry."
        return report
    resp = _tapir(port, command, payload) or {}
    if isinstance(resp, dict) and "error" in resp:
        report["error"] = resp["error"]
        return report
    items = resp.get("elements", []) if isinstance(resp, dict) else []
    guids = [e["elementId"]["guid"] for e in items if isinstance(e, dict) and "elementId" in e]
    item_errors = [e["error"] for e in items if isinstance(e, dict) and "error" in e]
    report["committed"] = bool(guids)
    report["createdGuids"] = guids
    if item_errors:
        report["itemErrors"] = item_errors
    if guids:
        report["verification"] = _verify(port, guids)
        if select:
            select_elements(port, guids)
    return report
