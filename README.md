# 🇮🇳 BharatText — Indian Language Text Analyzer

Analyze text in English, Hindi, Tamil, Malayalam and other Indian scripts: word,
sentence and paragraph counts, word frequency, word pairs, script detection,
document comparison and CSV export — through a Streamlit web app or the command line.

## Features

- **Unicode-correct tokenization** — Indic words are never broken at vowel signs or viramas
- **Sentence splitting** on `. ! ?` plus the Devanagari danda `।` / `॥` and Urdu `۔ ؟` (decimals like `3.14` stay intact)
- **Grapheme counting** — `क्षि` counts as one visible letter, not four code points
- **Script detection** for Devanagari, Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam, Urdu and Latin, including code-mixed text
- **Malayalam chillu normalization** — old-style (`ന്` + ZWJ) and atomic (`ൻ`) chillus count as the same word
- **Stopword filtering** for English, Hindi, Tamil and Malayalam
- **Statistics** — type-token ratio, hapax legomena, average/std-dev sentence length, word-length distribution
- **Compare two texts** — vocabulary overlap (Jaccard) and frequency similarity (cosine)
- **CSV export** in UTF-8 with BOM, so Excel shows Indian scripts correctly

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py            # web app at http://localhost:8501
```

Command line:

```bash
python -m bharattext samples/hindi.txt
python -m bharattext samples/tamil.txt --top 15 --stopwords --csv reports/
echo "Python is easy to learn. Python is powerful." | python -m bharattext -
```

Tests:

```bash
python -m pytest -q
```

## Project structure

```
bharattext/
├── app.py                  Streamlit web interface
├── bharattext/
│   ├── analyzer.py         tokenize, statistics, frequency, compare, CSV export
│   ├── scripts.py          Unicode block → script detection
│   ├── stopwords.py        stopword lists per script
│   └── __main__.py         command-line interface
├── samples/                English, Hindi, Tamil, Malayalam and code-mixed texts
├── tests/test_analyzer.py  pytest suite
└── .streamlit/config.toml  theme
```

## Design notes

**Why `regex` instead of `re`?** Indic words are base letters (Unicode category L) plus
combining marks (category M). Python's built-in `\w` skips combining marks, so
`re.findall(r"\w+", "हिन्दी")` returns fragments. The `regex` module supports `\p{M}`
and grapheme clusters (`\X`).

**Why Altair instead of Matplotlib for charts?** Matplotlib's default renderer does not
shape complex scripts, so Malayalam and Tamil conjuncts appear broken in chart labels.
Altair charts are drawn by the browser, which shapes Indian scripts correctly.

**Script ≠ language.** Devanagari is used for Hindi, Marathi, Nepali and Sanskrit, so the
app reports the script and lists the languages it may be.

## Known limitations

- Abbreviations such as "Dr." are treated as sentence ends.
- Words are counted as written: inflected forms (भाषा / भाषाओं, மொழி / மொழியை) are separate words. Stemming or lemmatization is a natural next step.
- Legacy non-Unicode Indian fonts (pre-Unicode ISCII or font-specific encodings) are not supported; files must be UTF-8 or UTF-16.
- Stopword lists are short and hand-picked.

## Ideas for the advanced version

- Stemming / lemmatization with [Indic NLP Library](https://github.com/anoopkunchukuttan/indic_nlp_library) or Stanza
- Named-entity recognition and part-of-speech tagging
- Transliteration between scripts
- Language identification that separates Hindi from Marathi
- Sentiment analysis with an Indic language model
