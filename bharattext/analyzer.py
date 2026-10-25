"""Core text analysis for BharatText.

Why the `regex` module and not `re`?
    Indic words are made of base letters (category L) *plus* combining vowel
    signs and viramas (category M). Python's built-in `\\w` does not match
    combining marks, so `re.findall(r"\\w+", "हिन्दी")` splits one word into
    fragments. `regex` supports `\\p{M}` and grapheme clusters (`\\X`).
"""

from __future__ import annotations

import io
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import regex

from . import stopwords as sw
from .scripts import LANGUAGE_OF, script_breakdown, script_of

# A word: letters / marks / digits, plus ZWJ and ZWNJ (used inside Indic words),
# optionally joined by an internal apostrophe or hyphen ("don't", "well-known").
_WORD_CHARS = r"[\p{L}\p{M}\p{N}‌‍]"
WORD_RE = regex.compile(rf"{_WORD_CHARS}+(?:['’\-]{_WORD_CHARS}+)*")

# Sentence terminators: . ! ? plus Devanagari danda । and double danda ॥,
# and the Urdu full stop ۔ and question mark ؟. A '.' only ends a sentence
# when followed by whitespace or end of text, so "3.14" stays intact.
SENTENCE_SPLIT_RE = regex.compile(r"[!?।॥۔؟]+|\.+(?=\s|$)|\n\s*\n")
PARAGRAPH_SPLIT_RE = regex.compile(r"\n\s*\n")
NUMERIC_RE = regex.compile(r"^\p{N}+$")
GRAPHEME_RE = regex.compile(r"\X")

# Malayalam chillu letters can be typed as consonant + virama + ZWJ (older
# input methods) or as atomic code points (Unicode 5.1+). NFC does not unify
# them, so we do it ourselves; otherwise "ഞാൻ" would count as two words.
_MALAYALAM_CHILLU = {
    "ണ്‍": "ൺ",
    "ന്‍": "ൻ",
    "ര്‍": "ർ",
    "ല്‍": "ൽ",
    "ള്‍": "ൾ",
    "ക്‍": "ൿ",
}


def normalize(text: str) -> str:
    """Unicode-normalize text so equal-looking words compare equal."""
    text = unicodedata.normalize("NFC", text)
    for old, new in _MALAYALAM_CHILLU.items():
        text = text.replace(old, new)
    return text.replace("\r\n", "\n").replace("\r", "\n")


_STOPWORDS = {normalize(w) for w in sw.ALL}


def tokenize(text: str) -> list[str]:
    """Split text into lowercase words. Lowercasing only affects cased scripts."""
    return [w.casefold() for w in WORD_RE.findall(normalize(text))]


def split_sentences(text: str) -> list[str]:
    parts = SENTENCE_SPLIT_RE.split(normalize(text))
    return [p.strip() for p in parts if p and WORD_RE.search(p)]


def split_paragraphs(text: str) -> list[str]:
    parts = PARAGRAPH_SPLIT_RE.split(normalize(text))
    return [p.strip() for p in parts if p.strip()]


def grapheme_len(s: str) -> int:
    """Length in user-perceived characters (e.g. 'क्षि' is 1 cluster, 4 code points)."""
    return len(GRAPHEME_RE.findall(s))


def decode_bytes(data: bytes) -> tuple[str, str]:
    """Decode an uploaded file. Returns (text, encoding used)."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16"
    for enc in ("utf-8-sig", "utf-16"):
        try:
            text = data.decode(enc)
            if enc == "utf-16" and not any(script_of(c) not in (None, "Other") for c in text[:500]):
                continue  # random bytes can "decode" as UTF-16 garbage
            return text, enc
        except UnicodeDecodeError:
            continue
    return data.decode("cp1252", errors="replace"), "cp1252 (fallback)"


@dataclass
class Options:
    remove_stopwords: bool = False
    exclude_numbers: bool = True
    min_word_length: int = 1  # in graphemes
    top_n: int = 20


@dataclass
class Analysis:
    text: str
    words: list[str]            # every word, in order
    filtered: list[str]         # words left after the frequency filters
    sentences: list[str]
    paragraphs: list[str]
    scripts: Counter
    options: Options = field(default_factory=Options)

    # ---- counts -------------------------------------------------------
    @property
    def word_count(self) -> int:
        return len(self.words)

    @property
    def unique_words(self) -> int:
        return len(set(self.words))

    @property
    def frequencies(self) -> Counter:
        return Counter(self.filtered)

    @property
    def dominant_script(self) -> str | None:
        return self.scripts.most_common(1)[0][0] if self.scripts else None

    # ---- tables -------------------------------------------------------
    def summary(self) -> dict:
        word_lens = np.array([grapheme_len(w) for w in self.words]) if self.words else np.array([0])
        sent_lens = np.array([len(WORD_RE.findall(s)) for s in self.sentences]) if self.sentences else np.array([0])
        freq = Counter(self.words)
        top = self.frequencies.most_common(1)
        script = self.dominant_script
        return {
            "Dominant script": script or "—",
            "Likely language(s)": LANGUAGE_OF.get(script, "—") if script else "—",
            "Characters (with spaces)": len(self.text),
            "Characters (no whitespace)": sum(1 for c in self.text if not c.isspace()),
            "Graphemes (visible letters)": grapheme_len(regex.sub(r"\s", "", self.text)),
            "Words": self.word_count,
            "Unique words": self.unique_words,
            "Sentences": len(self.sentences),
            "Paragraphs": len(self.paragraphs),
            "Avg word length (graphemes)": round(float(word_lens.mean()), 2) if self.words else 0,
            "Avg sentence length (words)": round(float(sent_lens.mean()), 2) if self.sentences else 0,
            "Longest sentence (words)": int(sent_lens.max()) if self.sentences else 0,
            "Sentence length std-dev": round(float(sent_lens.std()), 2) if self.sentences else 0,
            "Type-token ratio": round(self.unique_words / self.word_count, 3) if self.words else 0,
            "Hapax legomena (words used once)": sum(1 for c in freq.values() if c == 1),
            "Most frequent word": f"{top[0][0]} ({top[0][1]})" if top else "—",
            "Reading time (min, ~200 wpm)": round(self.word_count / 200, 1),
        }

    def summary_df(self) -> pd.DataFrame:
        return pd.DataFrame(list(self.summary().items()), columns=["Metric", "Value"])

    def frequency_df(self, n: int | None = None) -> pd.DataFrame:
        n = n or self.options.top_n
        rows = self.frequencies.most_common(n)
        total = max(len(self.filtered), 1)
        df = pd.DataFrame(rows, columns=["Word", "Count"])
        df["Percent"] = (df["Count"] / total * 100).round(2)
        df["Script"] = [script_of(w[0]) or "—" for w in df["Word"]]
        df.index = np.arange(1, len(df) + 1)
        df.index.name = "Rank"
        return df

    def bigram_df(self, n: int = 10) -> pd.DataFrame:
        pairs = Counter(zip(self.filtered, self.filtered[1:])).most_common(n)
        df = pd.DataFrame([(f"{a} {b}", c) for (a, b), c in pairs], columns=["Bigram", "Count"])
        df.index = np.arange(1, len(df) + 1)
        return df

    def word_length_df(self) -> pd.DataFrame:
        lengths = Counter(grapheme_len(w) for w in self.words)
        return pd.DataFrame(sorted(lengths.items()), columns=["Length (graphemes)", "Words"])

    def script_df(self) -> pd.DataFrame:
        total = sum(self.scripts.values()) or 1
        rows = [(s, c, round(c / total * 100, 1)) for s, c in self.scripts.most_common()]
        return pd.DataFrame(rows, columns=["Script", "Characters", "Percent"])


def _keep(word: str, opts: Options) -> bool:
    if opts.exclude_numbers and NUMERIC_RE.match(word):
        return False
    if opts.remove_stopwords and word in _STOPWORDS:
        return False
    return grapheme_len(word) >= opts.min_word_length


def analyze(text: str, options: Options | None = None) -> Analysis:
    opts = options or Options()
    text = normalize(text or "")
    words = tokenize(text)
    return Analysis(
        text=text,
        words=words,
        filtered=[w for w in words if _keep(w, opts)],
        sentences=split_sentences(text),
        paragraphs=split_paragraphs(text),
        scripts=script_breakdown(text),
        options=opts,
    )


# ---- comparison ------------------------------------------------------------

def compare(a: Analysis, b: Analysis) -> dict:
    """Vocabulary overlap (Jaccard) and frequency similarity (cosine)."""
    va, vb = set(a.filtered), set(b.filtered)
    union = va | vb
    jaccard = len(va & vb) / len(union) if union else 0.0

    vocab = sorted(union)
    fa, fb = a.frequencies, b.frequencies
    x = np.array([fa[w] for w in vocab], dtype=float)
    y = np.array([fb[w] for w in vocab], dtype=float)
    denom = np.linalg.norm(x) * np.linalg.norm(y)
    cosine = float(x @ y / denom) if denom else 0.0

    return {
        "jaccard": round(jaccard, 3),
        "cosine": round(cosine, 3),
        "shared": len(va & vb),
        "only_a": len(va - vb),
        "only_b": len(vb - va),
    }


def comparison_table(a: Analysis, b: Analysis, label_a="Text A", label_b="Text B") -> pd.DataFrame:
    sa, sb = a.summary(), b.summary()
    return pd.DataFrame({"Metric": list(sa), label_a: list(sa.values()), label_b: list(sb.values())})


def shared_words_df(a: Analysis, b: Analysis, n: int = 15) -> pd.DataFrame:
    fa, fb = a.frequencies, b.frequencies
    shared = set(fa) & set(fb)
    rows = sorted(((w, fa[w], fb[w]) for w in shared), key=lambda r: -(r[1] + r[2]))[:n]
    return pd.DataFrame(rows, columns=["Word", "Count in A", "Count in B"])


# ---- export ----------------------------------------------------------------

def to_csv_bytes(df: pd.DataFrame, index: bool = False) -> bytes:
    """CSV encoded as UTF-8 with BOM so Excel shows Indic scripts correctly."""
    buf = io.StringIO()
    df.to_csv(buf, index=index)
    return buf.getvalue().encode("utf-8-sig")
