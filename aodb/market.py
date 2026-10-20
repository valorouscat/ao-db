"""Live market data from the Albion Online Data Project (albion-online-data.com, crowd-sourced)."""
import gzip, json, os, random, sqlite3, time, urllib.error, urllib.parse, urllib.request
from contextlib import closing
from collections import defaultdict
from .core import AOError, label, money, fmt, table, resolve_item, recipes_of, returnable, item_value

API = "https://{srv}.albion-online-data.com/api/v2/stats/{kind}/{ids}.json"
SERVERS = ("europe", "west", "east")
CITIES = ["Caerleon", "Bridgewatch", "Fort Sterling", "Lymhurst", "Martlock", "Thetford", "Brecilien", "Black Market"]
SETUP_FEE, TAX_PREMIUM, TAX_NO_PREMIUM = 0.025, 0.04, 0.08
RETURN_RATES = "royal city: 15.2% (no focus) / 43.5% (focus); city bonus category: 24.8% / 47.9%"
CACHE_DIR = os.environ.get("AO_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "ao-db"))
CACHE_DB = os.path.join(CACHE_DIR, "market.sqlite")  # per-item answers + request log, shared by CLI runs and the MCP server
TTL = {"prices": 600, "history": 3600}  # seconds an answer counts as fresh (history is daily data)
URL_IDS_MAX = 3000  # characters of the id list per request (the API rejects very long URLs)
LIMITS = ((60, 170), (300, 285))  # API limit per IP: 180 requests/min and 300 per 5 min — keep a margin
WAIT = float(os.environ.get("AO_MARKET_WAIT", 30))  # max seconds one call waits on the rate limit before using cached prices
_mem = {}  # in-process copy of fresh per-item answers


class RateLimited(AOError):
    pass


def _db():
    os.makedirs(CACHE_DIR, exist_ok=True)
    con = sqlite3.connect(CACHE_DB, timeout=10)
    con.executescript("CREATE TABLE IF NOT EXISTS answers(key TEXT PRIMARY KEY, ts REAL, data TEXT);"
                      "CREATE TABLE IF NOT EXISTS requests(ts REAL);"
                      "CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v REAL);")
    return con


def _cached(keys):
    """{key: (rows, age in seconds)} of every stored answer, any age."""
    out = {}
    try:
        with closing(_db()) as con:
            for i in range(0, len(keys), 500):
                part = keys[i:i + 500]
                for k, ts, data in con.execute(f"SELECT key, ts, data FROM answers WHERE key IN ({','.join('?' * len(part))})", part):
                    out[k] = (json.loads(data), time.time() - ts)
    except (sqlite3.Error, OSError, ValueError):
        pass
    return out


def _store(answers):
    now = time.time()
    try:
        with closing(_db()) as con, con:
            con.executemany("INSERT OR REPLACE INTO answers VALUES (?,?,?)", [(k, now, json.dumps(v)) for k, v in answers.items()])
    except (sqlite3.Error, OSError):
        pass


def _wait_for_slot():
    """Seconds until the next request may go out: an active 429 cool-down or the client-side request budget."""
    now = time.time()
    try:
        with closing(_db()) as con, con:
            con.execute("DELETE FROM requests WHERE ts < ?", (now - max(w for w, _ in LIMITS),))
            cool = (con.execute("SELECT v FROM meta WHERE k='cooldown'").fetchone() or (0,))[0]
            wait = max(0.0, cool - now)
            for window, n in LIMITS:
                ts = [t for t, in con.execute("SELECT ts FROM requests WHERE ts > ? ORDER BY ts", (now - window,))]
                if len(ts) >= n:
                    wait = max(wait, ts[len(ts) - n] + window - now)
            return wait
    except (sqlite3.Error, OSError):
        return 0.0


def _log_request(cooldown=None):
    try:
        with closing(_db()) as con, con:
            if cooldown is None:
                con.execute("INSERT INTO requests VALUES (?)", (time.time(),))
            else:
                con.execute("INSERT OR REPLACE INTO meta VALUES ('cooldown', ?)", (time.time() + cooldown,))
    except (sqlite3.Error, OSError):
        pass


def _retry_after(err, attempt):
    try:
        return min(float(err.headers.get("Retry-After")), 120)
    except (TypeError, ValueError, AttributeError):
        return min(2 ** attempt * 2, 30) + random.uniform(0, 1)  # 2, 4, 8, 16 s + jitter


def _fetch(url):
    """One API answer: client-side throttling, Retry-After / exponential backoff on 429 and 5xx, retries on network errors,
    all within WAIT seconds; RateLimited when the limit doesn't clear in time."""
    deadline = time.time() + WAIT
    req = urllib.request.Request(url, headers={"User-Agent": "ao-db (github.com/valorouscat/ao-db)", "Accept-Encoding": "gzip"})
    for attempt in range(6):
        wait = _wait_for_slot()
        if wait:
            if time.time() + wait > deadline:
                raise RateLimited(f"Market API rate limit (HTTP 429) — cooling down for {wait:.0f} s more")
            time.sleep(wait)
        _log_request()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
            return json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise AOError(f"Market API request failed: {e}")
            pause = _retry_after(e, attempt)
            if e.code == 429:  # wait through the shared cool-down (other processes back off too instead of hammering the API)
                _log_request(cooldown=pause)
                continue
            if time.time() + pause > deadline:
                raise AOError(f"Market API request failed: {e}")
            time.sleep(pause)
        except (urllib.error.URLError, OSError, ValueError) as e:  # network failure is a user-facing condition
            if attempt >= 2 or time.time() + 2 ** attempt > deadline:
                raise AOError(f"Market API request failed: {e}")
            time.sleep(2 ** attempt)
    raise RateLimited("Market API rate limit (HTTP 429) — try again in a few minutes")


def _get(kind, ids, server, **params):
    """API rows for `ids`, cached per item: fresh answers come from the cache, only the missing items are requested (in
    URL-sized batches). When the API fails, items fall back to their last cached answer of any age (reported in WARNINGS);
    raises only when no item has any data."""
    if server not in SERVERS:
        raise AOError(f"server must be one of {SERVERS}")
    ids = list(dict.fromkeys(ids))
    params = {k: v for k, v in params.items() if v}
    base = f"{kind}|{server}|{json.dumps(params, sort_keys=True)}|"
    keys = {i: base + i for i in ids}
    now, got = time.time(), {}
    for i, k in keys.items():
        hit = _mem.get(k)
        if hit and now - hit[0] < TTL[kind]:
            got[i] = hit[1]
    disk = _cached([keys[i] for i in ids if i not in got])
    for i in ids:
        d = disk.get(keys[i])
        if i not in got and d and d[1] < TTL[kind]:
            got[i] = d[0]
            _mem[keys[i]] = (now - d[1], d[0])
    need = [i for i in ids if i not in got]
    batches, cur = [], []
    for i in need:
        if cur and len(",".join(cur + [i])) > URL_IDS_MAX:
            batches.append(cur)
            cur = []
        cur.append(i)
    batches += [cur] if cur else []
    error = None
    for b in batches:
        if error is None:
            url = API.format(srv=server, kind=kind, ids=urllib.parse.quote(",".join(b), safe=",@")) + "?" + urllib.parse.urlencode(params)
            try:
                rows = _fetch(url)
            except AOError as e:
                error = e
            else:
                per = {i: [] for i in b}
                for r in rows:
                    per.setdefault(r.get("item_id"), []).append(r)
                fresh = {i: per[i] for i in b}
                got.update(fresh)
                _store({keys[i]: v for i, v in fresh.items()})
                for i, v in fresh.items():
                    _mem[keys[i]] = (time.time(), v)
                continue
        # API unavailable: an older answer to the same question beats nothing
        stale = [(i, disk[keys[i]]) for i in b if keys[i] in disk]
        for i, (v, age) in stale:
            got[i] = v
        if stale:
            WARNINGS.append(f"{error} — used cached {kind} up to {max(a for _, (_, a) in stale) / 3600:.1f} h old for {len(stale)} item(s)")
        if len(stale) < len(b):
            WARNINGS.append(f"{error} — no {kind} data for {len(b) - len(stale)} item(s)")
    if error and not any(got.values()):
        raise error
    return [r for i in ids for r in got.get(i, [])]


def warnings_note():
    return ("\n\n⚠ " + "; ".join(dict.fromkeys(WARNINGS))) if WARNINGS else ""


LAST_PRICES = os.path.join(CACHE_DIR, "last_prices.json")  # {server|city|quality|item: [price, unix time, source]}


def _last_load():
    try:
        with open(LAST_PRICES, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _last_save(store):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = LAST_PRICES + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(store, fh)
        os.replace(tmp, LAST_PRICES)
    except OSError:
        pass


def _is_consumable(item_id):
    from .core import q1
    r = q1("SELECT kind, slot FROM items WHERE id=?", item_id)
    return bool(r) and (r["kind"] == "consumableitem" or r["slot"] in ("food", "potion"))


def _value_ratio(pairs, consumable):
    """Median market price / game item value over priced items of the same kind (equipment vs consumables)."""
    rs = sorted(p / v for i, p, v in pairs if v and p and _is_consumable(i) == consumable)
    return (rs[len(rs) // 2], len(rs)) if len(rs) >= 3 else ((10.0 if consumable else 20.0), 0)


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
    WARNINGS.clear()
    data = _get("prices", ids, server, locations=cities, qualities=quality)
    rows = [(label(d["item_id"]), d["city"], d["quality"], money(d["sell_price_min"] or None), _ago(d["sell_price_min_date"]),
             money(d["buy_price_max"] or None) if d["buy_price_max"] else "", _ago(d["buy_price_max_date"]) if d["buy_price_max"] else "")
            for d in data if d["sell_price_min"] or d["buy_price_max"]]
    return (f"## Market prices ({server}, quality {quality})\n\n" + table(rows, ["item", "city", "q", "sell min", "age", "buy max", "age"]) +
            "\n\n_Source: albion-online-data.com (crowd-sourced; check the age column)._" + warnings_note())


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
    WARNINGS.clear()
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
    return "\n".join(o) + warnings_note()


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
    WARNINGS.clear()
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
    return "\n".join(o) + warnings_note()


def best_city(item, server="europe", quality=1):
    """Where to buy cheapest / sell highest right now."""
    iid = resolve_item(item)
    WARNINGS.clear()
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
    return "\n".join(o) + warnings_note()


WARNINGS = []  # non-fatal API problems from the last price_map call, shown by callers


ABSURD_VALUE_RATIO = 300  # market prices run ~5-40× the game's item value; a lone listing far above is a troll listing


def _absurd(item_id, price):
    try:
        v = item_value(item_id)
    except Exception:
        return False
    return bool(v) and price > ABSURD_VALUE_RATIO * v


THIN = " ⚠ thin"  # source suffix: one listing / one or two cities and no sales history — treat the price as a guess
THIN_CITIES = 2
CRAFT_RETURN = 0.152  # resource return rate of a royal-city craft without focus


def is_thin(src):
    return THIN in (src or "")


def _artifact_craft(ids, server, city, quality):
    """{item: (craft cost, short breakdown)} for items whose recipe uses an artifact: artifact + materials (returnable ones
    at the no-focus return rate); items without such a recipe or with an unpriced ingredient are left out."""
    recs = {}
    for i in ids:
        r = (recipes_of(i) or [None])[0]
        if r and any("ARTEFACT" in m for m, _, _ in r["res"]):
            recs[i] = r
    if not recs:
        return {}
    saved = list(WARNINGS)  # the nested call resets WARNINGS
    try:
        mp = price_map(sorted({m for r in recs.values() for m, _, _ in r["res"]}), server, city, quality)
    finally:
        WARNINGS[:] = saved + [w for w in WARNINGS if w not in saved]
    out = {}
    for i, r in recs.items():
        lines = [(m, n * (1 if not returnable(mr) else 1 - CRAFT_RETURN), mp.get(m, (None,))[0]) for m, n, mr in r["res"]]
        if all(p for _, _, p in lines):
            art = sum(n * p for m, n, p in lines if "ARTEFACT" in m)
            out[i] = (sum(n * p for _, n, p in lines) + (r["silver"] or 0),
                      f"artifact {money(art)} + materials {money(sum(n * p for m, n, p in lines if 'ARTEFACT' not in m))}")
    return out


def price_map(ids, server="europe", city="Caerleon", quality=1, days=7, use_history=True, estimate=False):
    """{item_id: (unit_price, source)} — live sell_price_min, falling back to (or capped by) the recent average.
    API failures (e.g. rate limits) degrade to 'no data' and are reported in WARNINGS instead of raising.
    estimate=True fills the gaps: last known price of the item (any age), else game item value × the market/value ratio of
    priced items of the same kind; such sources start with '≈'."""
    ids = list(dict.fromkeys(ids))
    WARNINGS.clear()
    live, hist = {}, {}
    # one all-cities request: the price city's own listing + the cross-city median of fresh listings, which fills gaps and
    # catches single overpriced listings — needed most when the history request failed, else a troll listing goes through
    xcity = defaultdict(list)
    try:
        for d in _get("prices", ids, server, qualities=quality):
            if not d["sell_price_min"]:
                continue
            if d["city"] == city:
                live[d["item_id"]] = (d["sell_price_min"], d["sell_price_min_date"])
            age = _hours(d["sell_price_min_date"])
            if d["city"] != "Black Market" and age is not None and age < 24 * days:
                xcity[d["item_id"]].append(d["sell_price_min"])
    except AOError as e:
        WARNINGS.append(str(e))
    try:
        if use_history:
            hist.update({k[0]: v for k, v in history_avg(ids, server, city, quality, days).items()})
    except AOError as e:
        WARNINGS.append(f"history: {e}")
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
            out[i] = (lv[0], f"live {_ago(lv[1])}" + (THIN if not hv and len(xs) <= 1 else ""))
        elif hv and hv[0]:
            out[i] = (hv[0], f"{days}d avg")
        elif med:
            out[i] = (med, f"median of {len(xs)} other cities" + (THIN if len(xs) <= THIN_CITIES else ""))
        else:
            out[i] = (None, "no data")
    store, key = _last_load(), f"{server}|{city}|{quality}|"
    now = time.time()
    fresh = {i: v for i, v in out.items() if v[0] and not v[1].startswith("≈")}
    for i, (pr, src) in fresh.items():
        store[key + i] = [pr, now, src]
    if fresh:
        _last_save(store)
    # artifact gear: the artifact is most of the price, so artifact + materials beats item value × an average ratio, both
    # for unpriced items and to catch a lone listing far above what crafting it costs
    art = [i for i, (pr, src) in out.items() if (not pr and estimate) or (pr and THIN in src)]
    for i, (cost, parts) in _artifact_craft(art, server, city, quality).items():
        pr, src = out[i]
        if not pr:
            out[i] = (cost, f"≈ craft cost ({parts})")
        elif pr > 2 * cost:
            out[i] = (cost, f"≈ craft cost ({parts}); {src.replace(THIN, '')} {money(pr)} looks inflated")
    if estimate:
        pairs = [(i, pr, item_value(i)) for i, (pr, src) in fresh.items() if THIN not in src]
        pairs += [(k[len(key):], v[0], item_value(k[len(key):])) for k, v in store.items() if k.startswith(key) and k[len(key):] not in fresh][:400]
        for i, (pr, src) in list(out.items()):
            if pr:
                continue
            last = store.get(key + i)
            if last:
                out[i] = (last[0], f"≈ last known price, {(now - last[1]) / 3600:.0f}h old")
                continue
            v = item_value(i)
            if v:
                ratio, n = _value_ratio(pairs, _is_consumable(i))
                out[i] = (v * ratio, f"≈ estimate: item value {v:,.0f} × {ratio:.0f}" + (f" (median of {n} priced items)" if n else " (default ratio)"))
    return out
