"""Soft matching for the decision database (steer.py): rank records by relevance to free text.

Score = lexical BM25 (light stemming, so "plushies" meets "plushie") + meaning (a small local embedding
model, so "can the toys tip over" meets "fumos should not be affected by gravity") + a boost when the
text names one of a record's aliases or targets. Each part is scaled to 0..1 per query.

Meaning needs `pip install fastembed` (BAAI/bge-small-en-v1.5, ~70 MB, downloaded once, CPU). Without
it the ranking is lexical + aliases only, and says so on stderr once.

`serve` keeps the model loaded and answers one JSON request per stdin line (used by the
world-decisions omp extension, which spawns it once per omp process):
  in:  {"id": 1, "project": "C:/.../rp-world", "query": "...", "limit": 12, "exclude": ["S-0001"]}
  out: {"id": 1, "results": [{"id": "S-0042", "score": 0.81}, ...], "semantic": true}
"""
import fnmatch, json, math, pathlib, re, sys

MODEL = "BAAI/bge-small-en-v1.5"
W_LEX, W_SEM, W_HIT = 0.45, 0.55, 0.35
STOP = set(
    "a an and are as at be but by can could do does for from had has have he her his i if in into is it its "
    "just kinda like me my no not now of on or our so some than that the their them then there these they "
    "this to too up us was we were what when where which who will with would you your should make made".split())

_model = None
_model_tried = False


def stem(w):
    if w.endswith("ie"):  # plushie / plushies -> plushy
        w = w[:-2] + "y"
    for suf, rep in (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if len(w) > len(suf) + 2 and w.endswith(suf) and not w.endswith("ss"):
            return w[: -len(suf)] + rep
    return w


def near(a, b):
    """Same stem, or one a short extension of the other (drop/dropp, fall/fal): for alias matching."""
    if a == b:
        return True
    lo, hi = sorted((a, b), key=len)
    return len(lo) >= 4 and hi.startswith(lo) and len(hi) - len(lo) <= 2


def tokens(text):
    # Split camelCase and snake_case so "Fumo_Nikki" and "useGravity" become words too.
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def doc_text(r):
    return " ".join([r["topic"].replace("-", " "), " ".join(r.get("aliases", [])), " ".join(r.get("affects", [])),
                     " ".join(r.get("aspect", [])), r["decision"], " ".join(r.get("said", [])) if isinstance(
                         r.get("said"), list) else r.get("said", "")])


def embedder():
    global _model, _model_tried
    if not _model_tried:
        _model_tried = True
        try:
            from fastembed import TextEmbedding
            _model = TextEmbedding(MODEL)
        except Exception as e:  # missing package or offline first download: lexical only
            print(f"steer_rank: meaning-based matching off ({type(e).__name__}: {e}); pip install fastembed",
                  file=sys.stderr)
    return _model


def embed(texts):
    m = embedder()
    if m is None:
        return None
    import numpy as np
    v = np.array(list(m.embed(texts)), dtype="float32")
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


def bm25(query_toks, docs_toks, k1=1.4, b=0.75):
    n = len(docs_toks)
    avg = sum(len(d) for d in docs_toks) / max(n, 1)
    df = {}
    for d in docs_toks:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    out = []
    for d in docs_toks:
        tf, s = {}, 0.0
        for t in d:
            tf[t] = tf.get(t, 0) + 1
        for t in set(query_toks):
            if t in tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avg))
        out.append(s)
    return out


def hit(r, query, qtoks):
    """1.0 when the text names one of the record's aliases (stemmed word match), 0.6 when a word of the
    text matches one of its target globs (targets are often shared by many records, aliases are not)."""
    q = set(qtoks)
    for a in r.get("aliases", []):
        at = tokens(a)
        if at and all(any(near(t, x) for x in q) for t in at):
            return 1.0
    words = re.findall(r"[A-Za-z0-9_./\-]+", query)
    for p in r.get("targets", []):
        pl = p.lower()
        if any(fnmatch.fnmatch(w.lower(), pl) or (len(w) > 3 and w.lower() in pl) for w in words):
            return 0.6
    return 0.0


def scale(xs):
    hi = max(xs) if xs else 0
    return [x / hi if hi > 0 else 0.0 for x in xs]


class Index:
    """Per-project cache: records and their embeddings, rebuilt when the record set changes. Embeddings
    are also cached on disk (`cache` = <project>/STEER.emb.npz, keyed by each record's text hash), so
    only new or changed records are embedded again."""

    def __init__(self, cache=None):
        self.key, self.recs, self.toks, self.vecs, self.cache = None, [], [], None, cache

    def _embed_cached(self, texts):
        import hashlib
        hashes = [hashlib.sha1(t.encode("utf-8")).hexdigest()[:16] for t in texts]
        known = {}
        if self.cache and pathlib.Path(self.cache).exists():
            import numpy as np
            try:
                z = np.load(self.cache)
                known = dict(zip(z["hashes"].tolist(), z["vecs"]))
            except Exception:
                known = {}
        todo = [i for i, h in enumerate(hashes) if h not in known]
        if todo:
            fresh = embed([texts[i] for i in todo])
            if fresh is None:
                return None
            for i, v in zip(todo, fresh):
                known[hashes[i]] = v
        import numpy as np
        vecs = np.stack([known[h] for h in hashes]).astype("float32")
        if todo and self.cache:
            np.savez(self.cache, hashes=np.array(hashes), vecs=vecs)
        return vecs

    def load(self, recs):
        key = tuple((r["id"], r["decision"], tuple(r.get("aliases", []))) for r in recs)
        if key != self.key:
            self.key, self.recs = key, recs
            texts = [doc_text(r) for r in recs]
            self.toks = [tokens(t) for t in texts]
            self.vecs = self._embed_cached(texts) if recs and embedder() is not None else None
        return self

    def rank(self, query, limit=10, exclude=()):
        if not self.recs:
            return []
        qt = tokens(query)
        lex = scale(bm25(qt, self.toks))
        sem = [0.0] * len(self.recs)
        if self.vecs is not None:
            qv = embed([query])[0]
            raw = (self.vecs @ qv).tolist()
            lo = sorted(raw)[len(raw) // 2]  # median: below-median similarity counts as none
            sem = scale([max(0.0, x - lo) for x in raw])
        w_sem = W_SEM if self.vecs is not None else 0.0
        out = []
        for r, l, sc in zip(self.recs, lex, sem):
            if r["id"] in exclude:
                continue
            score = (W_LEX * l + w_sem * sc) / (W_LEX + w_sem) + W_HIT * hit(r, query, qt)
            out.append((round(score, 3), r))
        out.sort(key=lambda x: -x[0])
        return out[:limit]


def serve(load_current):
    """load_current(project_path) -> list of in-force records."""
    indexes = {}
    for line in sys.stdin:
        try:
            req = json.loads(line)
            proj = str(pathlib.Path(req["project"]).resolve())
            idx = indexes.setdefault(proj, Index(pathlib.Path(proj) / "STEER.emb.npz")).load(load_current(proj))
            res = idx.rank(req.get("query", ""), int(req.get("limit", 12)), set(req.get("exclude", [])))
            out = {"id": req.get("id"), "semantic": idx.vecs is not None,
                   "results": [{"id": r["id"], "score": s} for s, r in res]}
        except Exception as e:
            out = {"id": None, "error": f"{type(e).__name__}: {e}"}
            try:
                out["id"] = json.loads(line).get("id")
            except Exception:
                pass
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()
