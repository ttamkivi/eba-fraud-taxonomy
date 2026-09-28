"""Interpret raw extracted cells: names, qualifiers, definitions, sources, examples.

Every function here returns parts that are exact substrings of the raw cell text, so
build.py can prove that nothing was added or reworded: the parts must reassemble
into the original. Where a cell does not fit the patterns, the text stays in the
definition and nothing is guessed.
"""
import re
import unicodedata

QUALIFIER_OPENERS = ("includes", "optional", "does not", "only", "e.g.", "i.e.")
KEEP_PARENS = {"describe", "APT", "CFD"}


def split_name(raw):
    """'First party (optional element relevant, ...)' -> ('First party', 'optional element ...')."""
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", raw)
    if not m:
        return raw, None
    inner = m.group(2).strip()
    if inner in KEEP_PARENS or not inner.lower().startswith(QUALIFIER_OPENERS):
        return raw, None
    return m.group(1).strip(), inner


URL = r"https?://\S+?(?=[\s)\]]|\.?\s|\.?$|$)"
MARKER = r"(?:Definition based on the following source:|Sources?:)"


ABBREVIATIONS = ("Art", "Dr", "No", "Vol", "e.g", "i.e", "St", "Mr", "Mrs", "Ms", "Inc", "Ltd", "Co", "vs")


def _attribution_end(rest):
    """Where an attribution with no URL stops: at the next opening quotation mark, or at a
    full stop that ends a sentence (not an abbreviation or an initial), or at the end."""
    q = re.search(r"[“\"]", rest)
    limit = q.start() if q else len(rest)
    for m in re.finditer(r"\.(?=\s+[A-Z]|\s*$)", rest[:limit]):
        word = re.search(r"([\w.]+)$", rest[:m.start()])
        w = word.group(1) if word else ""
        if w in ABBREVIATIONS or re.fullmatch(r"[A-Z]", w):
            continue
        return m.start() + 1
    return limit


def split_sources(text):
    """Return (definition, [source dicts]). Sources are cut out of the text verbatim."""
    spans = []
    # 1. Marked sources: 'Source: <attribution> <url>' or 'Source: <attribution>.'
    for m in re.finditer(MARKER + r"\s*", text):
        start = m.start()
        rest = text[m.end():]
        um = re.search(URL, rest)
        stop = _attribution_end(rest)
        q = re.search(r"[“\"]", rest)
        if um and um.start() < (q.start() if q else len(rest)) and um.start() < 400:
            end = m.end() + um.end()
            attribution = rest[:um.start()].strip()
            url = um.group(0)
        else:
            end = m.end() + stop
            attribution = rest[:stop].strip()
            url = None
        attribution = re.sub(r"(?<=[\w)’'])\s*\d{1,2}$", "", attribution).rstrip(" .")
        spans.append((start, end, {"attribution": attribution, "url": url, "marker": m.group(0).strip()}))
    # 2. Unmarked attributions after a closing quotation mark: '...” EAST ‘Fraud Definitions’ https://...'
    for um in re.finditer(URL, text):
        if any(s <= um.start() < e for s, e, _ in spans):
            continue
        before = text[:um.start()]
        q = max(before.rfind("”"), before.rfind('"'))
        if q < 0 or um.start() - q > 300:
            continue
        attribution = text[q + 1:um.start()].strip()
        spans.append((q + 1, um.end(), {"attribution": attribution, "url": um.group(0), "marker": None}))
    spans.sort()
    definition, pos = [], 0
    for s, e, _ in spans:
        definition.append(text[pos:s])
        pos = e
    definition.append(text[pos:])
    d = re.sub(r"\s+", " ", " ".join(x.strip() for x in definition)).strip()
    d = re.sub(r"\s+([.,;:])", r"\1", d)
    return d, [x for _, _, x in spans]


def bullets(text):
    if "•" in text:
        return [b.strip() for b in text.split("•") if b.strip()]
    return [text.strip()] if text.strip() else []


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    for a, b in [("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("–", "-"), ("…", "...")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def match_labels(text, label_names):
    """Find label names in a 'possible labels/tags' cell. Longest names first, so a label
    containing commas is matched whole. Returns (matched names, leftover text)."""
    remaining = " " + norm(text) + " "
    found = []
    for name in sorted(label_names, key=len, reverse=True):
        k = " " + norm(name) + " "
        if k in remaining:
            found.append((remaining.find(k), name))
            remaining = remaining.replace(k, " | ", 1)
    leftover = re.sub(r"[\s|]+", " ", remaining).strip()
    return [n for _, n in sorted(found)], leftover
