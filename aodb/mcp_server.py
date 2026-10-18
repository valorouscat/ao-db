"""Zero-dependency MCP server (stdio, JSON-RPC 2.0, newline-delimited) exposing aodb.tools.TOOLS.

Register with Claude Code via the repo's .mcp.json, or manually:
    claude mcp add albion -- python3 -m aodb.mcp_server   (run from the repo root)
"""
import json, os, sys, traceback
from . import core
from .tools import TOOLS, call

SERVER_INFO = {"name": "albion", "version": "2.0.0"}
PROTOCOL = "2025-06-18"
MAX_CHARS = int(os.environ.get("AO_MCP_MAX_CHARS", "60000"))
INSTRUCTIONS = (
    "Albion Online game knowledge base built from ao-data/ao-bin-dumps (items, recipes, spells, mobs, loot, zones, all game text, "
    "every raw data file) plus live market prices. Workflow: `search` for anything vague → entity tools (`item`, `spell`, `mob`, `recipe`, "
    "`drops`, `zone`) → `doc` / `sql` for raw details. Check `patchnotes` so answers reflect the current patch (`info` shows data freshness). Item arguments accept IDs, names in any language and tier prefixes like '8.3 claymore'. "
    "Outputs are markdown; item icons: https://render.albiononline.com/v1/item/<ID>.png, spells: .../v1/spell/<ID>.png.")


def schema_for(t):
    props, req = {}, []
    for k, v in t["params"].items():
        p = {"type": v["type"], "description": v["description"]}
        if v["type"] == "array":
            p["items"] = {"type": "string", **({"enum": v["enum"]} if v["enum"] else {})}
        elif v["enum"]:
            p["enum"] = v["enum"]
        if v["default"] is not None:
            p["default"] = v["default"]
        props[k] = p
        if v["required"]:
            req.append(k)
    return {"type": "object", "properties": props, "required": req, "additionalProperties": False}


OPEN_WORLD = {"price", "history", "best_city", "craft_profit", "build_cost", "meta_builds", "update_patchnotes", "gear_check", "group_check", "pvp_check", "pvp_builds", "farm_plan", "build_optimizer"}
TOOL_LIST = [{"name": t["name"], "description": t["desc"], "inputSchema": schema_for(t),
              "annotations": {"readOnlyHint": t["name"] not in ("html", "save_note", "update_patchnotes", "record_outcome"),
                              "openWorldHint": t["name"] in OPEN_WORLD}}
             for t in TOOLS]


def handle(msg):
    method, mid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if mid is None:  # notification
        return None
    if method == "initialize":
        result = {"protocolVersion": params.get("protocolVersion") or PROTOCOL, "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": SERVER_INFO, "instructions": INSTRUCTIONS}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOL_LIST}
    elif method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        if name not in {t["name"] for t in TOOLS}:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"Unknown tool: {name}"}}
        try:
            text, err = call(name, args), False
        except core.AOError as e:
            text, err = f"error: {e}", True
        except TypeError as e:
            text, err = f"bad arguments: {e}", True
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            text, err = f"internal error: {type(e).__name__}: {e}", True
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + f"\n\n…[truncated {len(text) - MAX_CHARS} chars; narrow the query or lower limit]"
        result = {"content": [{"type": "text", "text": text}], "isError": err}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main():
    core.LANG = os.environ.get("AO_LANG", "en")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        else:
            out = [r for r in map(handle, msg) if r] if isinstance(msg, list) else handle(msg)
        if out:
            sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
