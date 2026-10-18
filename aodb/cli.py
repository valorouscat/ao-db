"""`ao` command line, generated from aodb.tools.TOOLS. Run `ao -h` / `ao <command> -h`."""
import argparse, signal, sys
from . import core
from .tools import TOOLS, call

PY = {"string": str, "integer": int, "number": float}


def build_parser():
    ap = argparse.ArgumentParser(prog="ao", description="Albion Online knowledge base (ao-bin-dumps) — search and analysis.")
    ap.add_argument("--lang", choices=["en", "ru"], default="en", help="preferred language for item names in labels")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for t in TOOLS:
        alias = [t["name"].replace("_", "-")] if "_" in t["name"] else []
        p = sub.add_parser(t["name"], aliases=alias, help=t["desc"], description=t["desc"])
        req = [k for k, v in t["params"].items() if v["required"]]
        for k, v in t["params"].items():
            h = v["description"] + (f" (default: {v['default']})" if v["default"] not in (None, False) else "")
            if v["required"]:
                # a single required text arg swallows the rest of the line: `ao item 6.1 broadsword`
                nargs = "+" if v["type"] == "array" or len(req) == 1 else None
                p.add_argument(k, nargs=nargs, help=h)
            elif k in ("query", "text") and not req:  # optional free text: `ao notes avalon chests`
                p.add_argument(k, nargs="*", help=h)
            elif v["type"] == "boolean":
                p.add_argument("--" + k.replace("_", "-"), dest=k, action=argparse.BooleanOptionalAction, default=v["default"], help=h)
            elif v["type"] == "array":
                p.add_argument("--" + k.replace("_", "-"), dest=k, help=h + " (comma separated)")
            else:
                p.add_argument("--" + k.replace("_", "-"), dest=k, type=PY[v["type"]], default=v["default"], choices=v["enum"], help=h)
    return ap


def main(argv=None):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    a = build_parser().parse_args(argv)
    core.LANG = a.lang
    a.cmd = a.cmd.replace("-", "_")
    t = next(t for t in TOOLS if t["name"] == a.cmd)
    args = {}
    for k, v in t["params"].items():
        val = getattr(a, k, None)
        if isinstance(val, list) and v["type"] != "array":
            val = " ".join(val) or None
        elif isinstance(val, str) and v["type"] == "array":
            val = [x.strip() for x in val.split(",") if x.strip()]
        args[k] = val
    try:
        print(call(a.cmd, args))
    except core.AOError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
