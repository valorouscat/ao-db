"""Official patch notes / dev updates from the Albion Online Steam news feed (appid 761890).

Stored as markdown in knowledge/patchnotes/ (committed, so history survives without network) and indexed into
knowledge.db (FTS5, rebuilt on demand). Update: `python3 -m aodb.patchnotes --update`.
"""
import argparse, datetime, glob, json, os, re, sqlite3, sys, time, urllib.request
from . import core
from .core import AOError, ROOT, table

APPID = 761890
API = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={app}&count=100&maxlength=0&feeds=steam_community_announcements{end}"
PN_DIR = os.path.join(ROOT, "knowledge", "patchnotes")
KDB = os.environ.get("AO_KDB", os.path.join(ROOT, "knowledge.db"))
KEEP = re.compile(r"changelog|patch|hotfix|update|dev ?talk|balance|release notes|known issues|roadmap|season \d+ (?:is|begins|starts)|is live|launch", re.I)
DROP = re.compile(r"% off|vanity|ambassador|spotlight|twitch|bundle|account security|sale\b|giveaway|livestream|stream|q&a|contest|survey|reminder", re.I)
_kcon = None


# ------------------------------------------------------------------ fetching
def _fetch(enddate=None):
    url = API.format(app=APPID, end=f"&enddate={enddate}" if enddate else "")
    req = urllib.request.Request(url, headers={"User-Agent": "ao-db (github.com/valorouscat/ao-db)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["appnews"]["newsitems"]


def bbcode_to_md(s):
    s = s.replace("\r", "")
    s = re.sub(r"\[img\].*?\[/img\]|\{STEAM_CLAN_IMAGE\}\S*|\[previewyoutube=[^\]]*\].*?\[/previewyoutube\]", "", s, flags=re.S | re.I)
    s = re.sub(r"\[h1\](.*?)\[/h1\]", r"\n## \1\n", s, flags=re.S | re.I)
    s = re.sub(r"\[h2\](.*?)\[/h2\]", r"\n### \1\n", s, flags=re.S | re.I)
    s = re.sub(r"\[h3\](.*?)\[/h3\]", r"\n### \1\n", s, flags=re.S | re.I)
    s = re.sub(r"\[/?b\]", "**", s, flags=re.I)
    s = re.sub(r"\[/?i\]", "_", s, flags=re.I)
    s = re.sub(r"\[quote\](.*?)\[/quote\]", lambda m: "\n> " + m.group(1).strip() + "\n", s, flags=re.S | re.I)
    # nested lists -> indented bullets
    out, depth = [], 0
    for tok in re.split(r"(\[list\]|\[/list\]|\[olist\]|\[/olist\]|\[\*\]|\[/\*\])", s, flags=re.I):
        t = tok.lower()
        if t in ("[list]", "[olist]"):
            depth += 1
        elif t in ("[/list]", "[/olist]"):
            depth = max(0, depth - 1)
            out.append("\n")
        elif t == "[*]":
            out.append("\n" + "  " * max(0, depth - 1) + "- ")
        elif t == "[/*]":
            continue
        else:
            out.append(tok.strip("\t") if depth else tok)
    s = "".join(out)
    s = re.sub(r"\[/?(?!url\b)[a-z0-9]+(?:=[^\]]*)?\]", "", s, flags=re.I)
    s = re.sub(r"\[url=([^\]]+)\](.*?)\[/url\]", r"[\2](\1)", s, flags=re.S | re.I)  # last, so "[text]" survives
    s = re.sub(r"[ \t]+\n", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def _slug(t):
    return re.sub(r"[^\w]+", "-", t.lower()).strip("-")[:70]


def relevant(item):
    t = item["title"]
    return bool(KEEP.search(t)) and not DROP.search(t) and (len(item["contents"]) > 1200 or re.search(r"changelog|hotfix", t, re.I))


def update(full=False, verbose=True):
    """Fetch new announcements (all history when full=True or the folder is empty); returns a summary."""
    os.makedirs(PN_DIR, exist_ok=True)
    have = {os.path.basename(p)[:10] + "|" + _read_meta(p).get("gid", "") for p in glob.glob(os.path.join(PN_DIR, "*.md"))}
    gids = {h.split("|", 1)[1] for h in have}
    newest = max((h[:10] for h in have), default=None)
    new, end, pages = [], None, 0
    try:
        while True:
            items = _fetch(end)
            pages += 1
            if not items:
                break
            for it in items:
                if relevant(it) and it["gid"] not in gids:
                    new.append(it)
            day = datetime.date.fromtimestamp(items[-1]["date"]).isoformat()
            if (not full and newest and day < newest) or len(items) < 2 or pages > 40:
                break
            end = items[-1]["date"] - 1
            time.sleep(0.3)
    except Exception as e:
        if not new:
            raise AOError(f"Steam news API failed: {e}")
    for it in new:
        day = datetime.date.fromtimestamp(it["date"]).isoformat()
        path = os.path.join(PN_DIR, f"{day}-{_slug(it['title'])}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"<!-- gid: {it['gid']} -->\n# {it['title']}\n\n_date: {day} · source: {it['url']}_\n\n{bbcode_to_md(it['contents'])}\n")
    reindex()
    msg = f"{len(new)} new patch note(s); {len(glob.glob(os.path.join(PN_DIR, '*.md')))} stored; latest: {latest_title()}"
    if verbose:
        print(msg, file=sys.stderr)
    return msg + ("\n" + "\n".join(f"- {datetime.date.fromtimestamp(i['date'])} {i['title']}" for i in new[:30]) if new else "")


def _read_meta(path):
    with open(path, encoding="utf-8") as fh:
        head = fh.read(600)
    m = re.search(r"gid: (\d+)", head)
    t = re.search(r"^# (.+)$", head, re.M)
    u = re.search(r"source: (\S+)_", head)
    return {"gid": m.group(1) if m else "", "title": t.group(1) if t else os.path.basename(path), "url": u.group(1) if u else ""}


# ------------------------------------------------------------------ index
def reindex():
    global _kcon
    _kcon = None
    tmp = KDB + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    db = sqlite3.connect(tmp)
    db.executescript("CREATE TABLE patches(file TEXT PRIMARY KEY, date TEXT, title TEXT, url TEXT, major INT);"
                     "CREATE TABLE sections(id INTEGER PRIMARY KEY, file TEXT, date TEXT, title TEXT, heading TEXT, text TEXT);"
                     "CREATE VIRTUAL TABLE sections_fts USING fts5(title, heading, text, content='sections', content_rowid='id', "
                     "tokenize='unicode61 remove_diacritics 2');")
    for p in sorted(glob.glob(os.path.join(PN_DIR, "*.md"))):
        f = os.path.basename(p)
        meta = _read_meta(p)
        with open(p, encoding="utf-8") as fh:
            body = fh.read().split("\n", 4)[-1]
        # major content updates: "Changelog: Dragonfire Update", "Dragonfire is Live!" (not "... Patch 3 is Live", not dev talks)
        major = 1 if (re.match(r"^Changelog: [\w' -]+ Update$", meta["title"]) or re.search(r"\bis live!?$", meta["title"], re.I)) \
            and not re.search(r"patch \d|hotfix|dev talk|season", meta["title"], re.I) else 0
        db.execute("INSERT INTO patches VALUES(?,?,?,?,?)", (f, f[:10], meta["title"], meta["url"], major))
        heading, buf = "", []

        def flush():
            text = "\n".join(buf).strip()
            if len(text) > 30:
                db.execute("INSERT INTO sections(file,date,title,heading,text) VALUES(?,?,?,?,?)", (f, f[:10], meta["title"], heading, text))

        for line in body.splitlines():
            if line.startswith("## ") or line.startswith("### "):
                flush()
                heading, buf = line.lstrip("# ").strip(), []
            else:
                buf.append(line)
        flush()
    db.execute("INSERT INTO sections_fts(sections_fts) VALUES('rebuild')")
    db.commit()
    db.close()
    os.replace(tmp, KDB)


def kdb():
    global _kcon
    if _kcon is None:
        newest = max((os.path.getmtime(p) for p in glob.glob(os.path.join(PN_DIR, "*.md"))), default=0)
        if not os.path.exists(KDB) or os.path.getmtime(KDB) < newest:
            if not newest:
                raise AOError("No patch notes stored yet. Run update_patchnotes (python3 -m aodb.patchnotes --update --full).")
            reindex()
        _kcon = sqlite3.connect(KDB, check_same_thread=False)
        _kcon.row_factory = sqlite3.Row
    return _kcon


def latest_title():
    try:
        r = kdb().execute("SELECT date, title FROM patches WHERE title LIKE '%Changelog%' OR title LIKE '%Patch%' ORDER BY date DESC LIMIT 1").fetchone()
        return f"{r['title']} ({r['date']})" if r else "unknown"
    except AOError:
        return "unknown (no patch notes stored)"


def current_patch():
    """(date, title) of the newest changelog-like post — the 'as of' for freshness checks."""
    r = kdb().execute("SELECT date, title FROM patches WHERE title LIKE '%Changelog%' OR title LIKE '%Patch%' OR title LIKE '%Hotfix%' "
                      "ORDER BY date DESC LIMIT 1").fetchone()
    return (r["date"], r["title"]) if r else (None, None)


def last_major():
    r = kdb().execute("SELECT date, title FROM patches WHERE major=1 ORDER BY date DESC LIMIT 1").fetchone()
    return (r["date"], r["title"]) if r else (None, None)


# ------------------------------------------------------------------ tools
def top_lines(query, limit=4):
    """One line per most relevant section (newest first) — compact 'recent changes' for other tools."""
    try:
        rows = _select(query, None, limit)
    except (AOError, sqlite3.OperationalError):
        return ""
    return "\n".join(f"- {r['date']} **{r['title']}** › {r['heading'] or 'intro'}: {_snippet(r['text'], query.split()[0], 220)} ([src]({r['url']}))"
                     for r in rows)


def _select(query, since, limit):
    """Most relevant sections (heading match > exact phrase > all words > prefixes > any word), newest first."""
    words = core.fts_query(query, prefix=False).split()
    phrase = f'"{" ".join(w.strip(chr(34)) for w in words)}"'
    # a section whose heading names the topic is the most on-topic source; then phrase / all words / prefixes
    tiers = [f"heading : {phrase}"] + ([phrase] if len(words) > 1 else []) + [" ".join(words), core.fts_query(query)]
    if len(words) > 1:
        tiers.append(" OR ".join(words))
    cond, extra = (" AND s.date >= ?", [since]) if since else ("", [])
    picked, seen = [], set()
    for fq in tiers:
        order = "s.date DESC" if fq.startswith("heading") else "r"
        rows = kdb().execute(f"SELECT s.*, p.url, bm25(sections_fts, 2, 10, 1) r FROM sections_fts f JOIN sections s ON s.id=f.rowid "
                             f"JOIN patches p ON p.file=s.file WHERE sections_fts MATCH ?{cond} ORDER BY {order} LIMIT ?",
                             [fq] + extra + [max(limit * 2, 10)]).fetchall()
        for r in rows:
            if r["id"] not in seen:
                seen.add(r["id"])
                picked.append(r)
        if len(picked) >= limit:
            break
    if not picked:
        return []
    rows = sorted(picked[:max(limit * 2, 10)], key=lambda r: r["date"], reverse=True)[:limit]
    if rows and picked[0]["id"] not in {r["id"] for r in rows}:
        rows[-1] = picked[0]  # never drop the single most relevant section
    return rows


def patchnotes(query, since=None, limit=6, max_chars=1500):
    """Most relevant sections, shown newest first."""
    rows = _select(query, since, limit)
    if not rows:
        return f"No patch notes mention {query!r}" + (f" since {since}" if since else "") + f". Latest stored: {latest_title()}."
    o = [f"## Patch notes about “{query}” (most relevant, newest first; latest stored patch: {latest_title()})", ""]
    for r in rows:
        text = r["text"] if len(r["text"]) <= max_chars else r["text"][:max_chars] + " …"
        o.append(f"### {r['date']} — {r['title']} › {r['heading'] or '(intro)'}\n{text}\n\n[source]({r['url']})\n")
    o.append("_When patch notes disagree, the newest one is in force. Check later hotfixes too._")
    return "\n".join(o)


def latest_patches(limit=12):
    rows = kdb().execute("SELECT date, title, url, major FROM patches ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    d, t = last_major()
    return (f"## Latest official posts (current patch: {latest_title()}; last major update: {t} {d})\n\n" +
            table([(r["date"], ("★ " if r["major"] else "") + r["title"], r["url"]) for r in rows], ["date", "title", "link"]))


def _indent(ln):
    return len(ln) - len(ln.lstrip(" "))


def _snippet(text, term, n=300):
    """Line mentioning term with its context: the nearest heading-like line above it and the nested lines under it."""
    raw = text.splitlines()
    idx = next((i for i, ln in enumerate(raw) if term.lower() in ln.lower()), None)
    clean = lambda ln: ln.strip().strip("-*_> ").strip()
    if idx is None:
        s = " · ".join(clean(ln) for ln in raw if clean(ln))
        return s[:n] + ("…" if len(s) > n else "")
    line, ind = raw[idx], _indent(raw[idx])
    ctx = ""
    for ln in reversed(raw[:idx]):  # parent bullet (less indented) or bold label
        if clean(ln) and (_indent(ln) < ind and ln.strip().startswith("-") or ln.strip().startswith("**")):
            ctx = clean(ln)
            break
    kids = []
    for ln in raw[idx + 1:]:
        if not ln.strip():
            if kids:
                break
            continue
        if line.strip().startswith("-") and _indent(ln) <= ind:
            break
        if line.strip().startswith("**") and ln.strip().startswith("**"):
            break
        kids.append(clean(ln))
        if len(kids) >= 5:
            break
    head = clean(line)
    s = (f"{ctx} → " if ctx and ctx != head else "") + head + (": " + "; ".join(kids) if kids else "")
    return s[:n] + ("…" if len(s) > n else "")


def recent_changes(term, limit=3):
    """Short 'recent patch changes' lines mentioning term, for entity cards. Empty string when nothing/no data."""
    if not term or len(term) < 3:
        return ""
    try:
        rows = kdb().execute("SELECT s.date, s.title, s.heading, s.text, p.url FROM sections_fts f JOIN sections s ON s.id=f.rowid "
                             "JOIN patches p ON p.file=s.file WHERE sections_fts MATCH ? ORDER BY s.date DESC LIMIT 20",
                             (f'"{term}"',)).fetchall()
    except (AOError, sqlite3.OperationalError):
        return ""
    out, seen = [], set()
    for r in rows:
        snippet = _snippet(r["text"], term)
        key = (r["date"], snippet)
        if key not in seen:
            seen.add(key)
            out.append(f"- {r['date']} **{r['title']}** › {r['heading'] or 'intro'}: {snippet} ([src]({r['url']}))")
        if len(out) >= limit:
            break
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--update", action="store_true", help="fetch new posts")
    ap.add_argument("--full", action="store_true", help="fetch the whole history")
    ap.add_argument("--reindex", action="store_true")
    a = ap.parse_args()
    if a.update or a.full:
        print(update(full=a.full, verbose=False))
    if a.reindex:
        reindex()
        print("reindexed", KDB)


if __name__ == "__main__":
    main()
