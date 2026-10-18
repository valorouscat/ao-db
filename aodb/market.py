"""Live market data from the Albion Online Data Project (albion-online-data.com, crowd-sourced)."""
import hashlib, json, os, time, urllib.error, urllib.parse, urllib.request
from collections import defaultdict
from .core import AOError, label, money, fmt, table, resolve_item, recipes_of, returnable, item_value

API = "https://{srv}.albion-online-data.com/api/v2/stats/{kind}/{ids}.json"
SERVERS = ("europe", "west", "east")
CITIES = ["Caerleon", "Bridgewatch", "Fort Sterling", "Lymhurst", "Martlock", "Thetford", "Brecilien", "Black Market"]
SETUP_FEE, TAX_PREMIUM, TAX_NO_PREMIUM = 0.025, 0.04, 0.08
RETURN_RATES = "royal city: 15.2% (no focus) / 43.5% (focus); city bonus category: 24.8% / 47.9%"
_cache = {}
CACHE_DIR = os.environ.get("AO_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "ao-db"))


def _get(kind, ids, server, **params):
    if server not in SERVERS:
        raise AOError(f"server must be one of {SERVERS}")
    url = API.format(srv=server, kind=kind, ids=urllib.parse.quote(",".join(ids), safe=",@")) + "?" + urllib.parse.urlencode(
        {k: v for k, v in params.items() if v})
    hit = _cache.get(url)
    if hit and time.time() - hit[0] < 300:
        return hit[1]
    cpath = os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".json")
    try:  # disk cache shared by CLI runs and the MCP server
        if time.time() - os.path.getmtime(cpath) < 600:
            with open(cpath, encoding="utf-8") as fh:
                data = json.load(fh)
            _cache[url] = (time.time(), data)
            return data
    except (OSError, ValueError):
        pass
    req = urllib.request.Request(url, headers={"User-Agent": "ao-db (github.com/valorouscat/ao-db)", "Accept-Encoding": "identity"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 1:  # API limit: 180 req/min, 300 req/5 min (shared per IP)
                time.sleep(3)
                continue
            if e.code == 429:
                raise AOError("Market API rate limit (HTTP 429) — try again in a few minutes")
            raise AOError(f"Market API request failed: {e}")
        except Exception as e:  # network failure is a user-facing condition
            raise AOError(f"Market API request failed: {e}")
    _cache[url] = (time.time(), data)
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cpath, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
    except OSError:
        pass
    return data


def _hours(ts):
    if not ts or ts.startswith("0001"):
        return None
    try:
        return (time.time() - time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) + time.timezone) / 3600
    except ValueError:
        return None


def _ago(ts):
    if not ts or ts.startswith("0001"):
        return ""
    try:
        h = (time.time() - time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) + time.timezone) / 3600
    except ValueError:
        return ts
    return f"{h:.0f}h ago" if h < 48 else f"{h / 24:.0f}d ago"


def price(items, server="europe", cities=None, quality=1):
    ids = [resolve_item(x) for x in items]
    data = _get("prices", ids, server, locations=cities, qualities=quality)
    rows = [(label(d["item_id"]), d["city"], d["quality"], money(d["sell_price_min"] or None), _ago(d["sell_price_min_date"]),
             money(d["buy_price_max"] or None) if d["buy_price_max"] else "", _ago(d["buy_price_max_date"]) if d["buy_price_max"] else "")
            for d in data if d["sell_price_min"] or d["buy_price_max"]]
    return (f"## Market prices ({server}, quality {quality})\n\n" + table(rows, ["item", "city", "q", "sell min", "age", "buy max", "age"]) +
            "\n\n_Source: albion-online-data.com (crowd-sourced; check the age column)._")


def history_avg(ids, server, cities=None, quality=1, days=7):
    """{(item, city): (avg_price, daily_volume)} over the last `days` days."""
    data = _get("history", ids, server, locations=cities, qualities=quality, **{"time-scale": 24})
    out = {}
    for d in data:
        pts = d.get("data") or []
        pts = pts[-days:]
        if pts:
            vol = sum(p["item_count"] for p in pts)
            avg = sum(p["avg_price"] * p["item_count"] for p in pts) / vol if vol else None
            out[(d["item_id"], d["location"])] = (avg, vol / len(pts))
    return out


def history(item, server="europe", cities=None, quality=1, days=14):
    iid = resolve_item(item)
    data = _get("history", [iid], server, locations=cities, qualities=quality, **{"time-scale": 24})
    o = [f"## Price history: {label(iid)} ({server}, quality {quality}, last {days} days)\n"]
    summary = []
    for d in data:
        pts = (d.get("data") or [])[-days:]
        if not pts:
            continue
        vol = sum(p["item_count"] for p in pts)
        avg = sum(p["avg_price"] * p["item_count"] for p in pts) / vol if vol else 0
        first, last = pts[0]["avg_price"], pts[-1]["avg_price"]
        summary.append((d["location"], money(avg), f"{vol / len(pts):.0f}", money(min(p["avg_price"] for p in pts)),
                        money(max(p["avg_price"] for p in pts)), f"{(last - first) / first:+.0%}" if first else ""))
    o.append(table(sorted(summary, key=lambda r: r[0]), ["city", "avg price", "sold/day", "min day", "max day", "trend"]))
    return "\n".join(o)


def craft_profit(item, server="europe", city="Caerleon", sell_city=None, return_rate=None, focus=False, station_fee=0.0,
                 premium=True, qty=1, recipe_no=0, days=7):
    """Profit estimate for crafting `item` from bought (refined) materials in one city."""
    iid = resolve_item(item)
    recs = recipes_of(iid)
    if not recs:
        raise AOError(f"{label(iid)} has no crafting recipe")
    r = recs[min(recipe_no, len(recs) - 1)]
    rr = (0.435 if focus else 0.152) if return_rate is None else (return_rate / 100 if return_rate > 1 else return_rate)
    sell_city = sell_city or city
    mats = r["res"]
    ids = [iid] + [m[0] for m in mats]
    cities = ",".join(sorted({city, sell_city}))
    live = {(d["item_id"], d["city"]): d for d in _get("prices", ids, server, locations=cities, qualities=1)}
    hist = history_avg(ids, server, cities, 1, days)

    def unit(i, c, want="buy"):
        """Instant price to buy (sell_price_min); fall back to recent average."""
        d = live.get((i, c))
        if d and d["sell_price_min"]:
            return d["sell_price_min"], "live min", _ago(d["sell_price_min_date"])
        h = hist.get((i, c))
        return (h[0], f"{days}d avg", "") if h and h[0] else (None, "no data", "")

    crafts = qty / r["amount"]
    rows, cost, missing = [], 0.0, []
    for rid, cnt, mr in mats:
        p, src, age = unit(rid, city)
        eff = cnt * ((1 - rr) if returnable(mr) else 1)
        line = None if p is None else p * eff * crafts
        cost += line or 0
        if p is None:
            missing.append(rid)
        rows.append((label(rid), cnt, fmt(eff), money(p), src + (f" {age}" if age else ""), money(line)))
    iv = item_value(iid) or 0
    fee = iv * 0.1125 * station_fee / 100 * crafts
    silver = (r["silver"] or 0) * crafts
    sp, ssrc, sage = unit(iid, sell_city)
    hv = hist.get((iid, sell_city))
    if sp and hv and hv[0] and sp > hv[0] * 1.25:  # lone overpriced listing: use the realistic recent average
        sp, ssrc, sage = hv[0], f"{days}d avg; live min {money(sp)} looks inflated", ""
    tax = TAX_PREMIUM if premium else TAX_NO_PREMIUM
    revenue = None if sp is None else sp * qty * (1 - tax - SETUP_FEE)
    total_cost = cost + fee + silver
    o = [f"## Craft profit: {label(iid)} ×{fmt(float(qty))} ({server})\n",
         f"- buy materials in **{city}**, sell in **{sell_city}** · return rate **{rr:.1%}** ({'focus' if focus else 'no focus'}) · "
         f"{'premium' if premium else 'no premium'} tax {tax:.0%} + setup {SETUP_FEE:.1%}",
         f"- crafts: {fmt(crafts)} (recipe yields {r['amount']}) · focus per craft: {fmt(r['focus'])}" + (f" · total focus {fmt(r['focus'] * crafts)}" if focus else ""),
         "\n" + table(rows, ["material", "per craft", "effective", "unit price", "source", "total"]),
         f"\n| | silver |\n|---|---|\n| materials | {money(cost)} |\n| station fee ({fmt(station_fee)}/100 nutrition, item value {fmt(iv)}) | {money(fee)} |"
         + (f"\n| recipe silver | {money(silver)} |" if silver else "") +
         f"\n| **total cost** | **{money(total_cost)}** |\n| sell price ({ssrc}{' ' + sage if sage else ''}) | {money(sp)} each |"
         f"\n| revenue after tax | {money(revenue)} |"]
    if revenue is not None and not missing:
        profit = revenue - total_cost
        o.append(f"| **profit** | **{money(profit)}** ({profit / total_cost:+.1%}) · {money(profit / qty)} per item |" if total_cost else "")
    if hv:
        o.append(f"\nSell-city {days}d average {money(hv[0])}, ~{hv[1]:.0f} sold/day.")
    if missing:
        o.append("\n⚠ No price data for: " + ", ".join(f"`{m}`" for m in missing) + " — profit not computed.")
    o.append(f"\n_Return-rate presets: {RETURN_RATES}. Prices are crowd-sourced; verify before big investments._")
    return "\n".join(o)


def best_city(item, server="europe", quality=1):
    """Where to buy cheapest / sell highest right now."""
    iid = resolve_item(item)
    data = [d for d in _get("prices", [iid], server, qualities=quality) if d["sell_price_min"] or d["buy_price_max"]]
    sells = sorted((d for d in data if d["sell_price_min"]), key=lambda d: d["sell_price_min"])
    buys = sorted((d for d in data if d["buy_price_max"]), key=lambda d: -d["buy_price_max"])
    o = [f"## {label(iid)} — best cities ({server}, quality {quality})\n",
         "### Cheapest to buy (sell orders)\n" + table([(d["city"], money(d["sell_price_min"]), _ago(d["sell_price_min_date"])) for d in sells[:8]],
                                                     ["city", "price", "age"]),
         "\n### Best to sell instantly (buy orders)\n" + table([(d["city"], money(d["buy_price_max"]), _ago(d["buy_price_max_date"])) for d in buys[:8]],
                                                              ["city", "price", "age"])]
    if sells and buys:
        s, b = sells[0], buys[0]
        net = b["buy_price_max"] * (1 - TAX_PREMIUM) - s["sell_price_min"]
        o.append(f"\nFlip: buy in {s['city']} at {money(s['sell_price_min'])} → sell to buy order in {b['city']} at {money(b['buy_price_max'])}: "
                 f"**{money(net)}** after 4% tax (transport risk not included).")
    return "\n".join(o)


WARNINGS = []  # non-fatal API problems from the last price_map call, shown by callers


ABSURD_VALUE_RATIO = 300  # market prices run ~5-40× the game's item value; a lone listing far above is a troll listing


def _absurd(item_id, price):
    try:
        v = item_value(item_id)
    except Exception:
        return False
    return bool(v) and price > ABSURD_VALUE_RATIO * v


def price_map(ids, server="europe", city="Caerleon", quality=1, days=7, use_history=True):
    """{item_id: (unit_price, source)} — live sell_price_min, falling back to (or capped by) the recent average.
    API failures (e.g. rate limits) degrade to 'no data' and are reported in WARNINGS instead of raising."""
    ids = list(dict.fromkeys(ids))
    WARNINGS.clear()
    live, hist = {}, {}
    live_ok = True
    for i in range(0, len(ids), 80):
        try:
            for d in _get("prices", ids[i:i + 80], server, locations=city, qualities=quality):
                if d["sell_price_min"]:
                    live[d["item_id"]] = (d["sell_price_min"], d["sell_price_min_date"])
        except AOError as e:
            WARNINGS.append(str(e))
            live_ok = False
            break
    for i in range(0, len(ids), 80) if use_history and live_ok else ():
        try:
            hist.update({k[0]: v for k, v in history_avg(ids[i:i + 80], server, city, quality, days).items()})
        except AOError as e:
            WARNINGS.append(f"history: {e}")
            break
    # cross-city median of fresh listings: fills gaps and catches single overpriced listings — still needed (most of all)
    # when the history request failed, otherwise a troll listing goes through unchecked
    xcity = defaultdict(list)
    for i in range(0, len(ids), 80) if live_ok else ():
        try:
            for d in _get("prices", ids[i:i + 80], server, qualities=quality):
                age = _hours(d["sell_price_min_date"])
                if d["sell_price_min"] and d["city"] != "Black Market" and age is not None and age < 24 * days:
                    xcity[d["item_id"]].append(d["sell_price_min"])
        except AOError as e:
            WARNINGS.append(f"cross-city: {e}")
            break
    out = {}
    for i in ids:
        lv, hv = live.get(i), hist.get(i)
        xs = sorted(xcity.get(i, []))
        med = xs[len(xs) // 2] if xs else None
        ref = hv[0] if hv and hv[0] else med
        if lv and ref and lv[0] > ref * 1.25:
            out[i] = (ref, f"{'%dd avg' % days if hv and hv[0] else 'median of %d cities' % len(xs)} (live {money(lv[0])} inflated)")
        elif lv and not ref and _absurd(i, lv[0]):  # nothing to compare with and far above any normal market/value ratio
            out[i] = (None, f"live {money(lv[0])} ignored (×{lv[0] / item_value(i):,.0f} item value, no reference price)")
        elif lv:
            out[i] = (lv[0], f"live {_ago(lv[1])}")
        elif hv and hv[0]:
            out[i] = (hv[0], f"{days}d avg")
        elif med:
            out[i] = (med, f"median of {len(xs)} other cities")
        else:
            out[i] = (None, "no data")
    return out
