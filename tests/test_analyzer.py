import io
from pathlib import Path

import pandas as pd
import pytest

from bharattext import Options, analyze, compare, decode_bytes, to_csv_bytes, tokenize
from bharattext.analyzer import grapheme_len, normalize, split_sentences
from bharattext.scripts import dominant_script, script_of

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


# -- the worked example from the project brief --------------------------------
def test_english_example():
    r = analyze("Python is easy to learn. Python is powerful. I love Python.")
    assert r.word_count == 11
    assert r.unique_words == 8
    assert len(r.sentences) == 3
    assert r.frequencies.most_common(1) == [("python", 3)]


# -- tokenization ---------------------------------------------------------------
def test_hindi_words_not_split_at_vowel_signs():
    # Plain `re` with \w would break these at matras and viramas.
    assert tokenize("हिन्दी भाषा सुंदर है") == ["हिन्दी", "भाषा", "सुंदर", "है"]


def test_tamil_words():
    assert tokenize("தமிழ் ஒரு பழமையான மொழி.") == ["தமிழ்", "ஒரு", "பழமையான", "மொழி"]


def test_malayalam_words():
    assert tokenize("മലയാളം കേരളത്തിന്റെ ഭാഷയാണ്.") == ["മലയാളം", "കേരളത്തിന്റെ", "ഭാഷയാണ്"]


def test_malayalam_old_style_chillu_is_normalized():
    old_style = "ഞാന്‍"   # na + virama + ZWJ
    atomic = "ഞാൻ"             # U+0D7B chillu n
    assert normalize(old_style) == atomic
    assert analyze(f"{old_style} {atomic}").unique_words == 1


def test_english_apostrophes_and_hyphens_stay_in_word():
    assert tokenize("Don't stop well-known code-mixing") == ["don't", "stop", "well-known", "code-mixing"]


def test_case_insensitive_english_only():
    assert tokenize("India INDIA india") == ["india"] * 3


def test_indic_digits_are_numbers():
    r = analyze("भाषा २०२६ भाषा 2026", Options(exclude_numbers=True))
    assert r.word_count == 4
    assert dict(r.frequencies) == {"भाषा": 2}


# -- sentences ------------------------------------------------------------------
def test_danda_splits_sentences():
    assert len(split_sentences("भारत एक देश है। यहाँ कई भाषाएँ हैं॥ ठीक?")) == 3


def test_decimal_point_does_not_split():
    assert len(split_sentences("Pi is 3.14 roughly. Yes.")) == 2


def test_punctuation_only_fragments_are_not_sentences():
    assert len(split_sentences("Hello!!! ... ???")) == 1


# -- graphemes & scripts ----------------------------------------------------------
def test_grapheme_length_counts_visible_letters():
    assert len("नमस्ते") == 6           # code points
    assert grapheme_len("नमस्ते") < 6    # न, म, स्ते  (conjunct is one cluster)


@pytest.mark.parametrize("ch,script", [
    ("a", "Latin"), ("क", "Devanagari"), ("த", "Tamil"), ("മ", "Malayalam"),
    ("ক", "Bengali"), ("ਪ", "Gurmukhi"), ("ગ", "Gujarati"), ("ତ", "Odia"),
    ("త", "Telugu"), ("ಕ", "Kannada"), ("ا", "Arabic"), (".", None), (" ", None),
])
def test_script_of(ch, script):
    assert script_of(ch) == script


@pytest.mark.parametrize("name,script", [
    ("english.txt", "Latin"), ("hindi.txt", "Devanagari"),
    ("tamil.txt", "Tamil"), ("malayalam.txt", "Malayalam"),
])
def test_samples_detect_their_script(name, script):
    assert dominant_script((SAMPLES / name).read_text(encoding="utf-8")) == script


# -- filters ----------------------------------------------------------------------
def test_stopwords_removed_per_language():
    opts = Options(remove_stopwords=True)
    assert "the" not in analyze("the cat and the hat", opts).frequencies
    assert "है" not in analyze("भारत एक देश है", opts).frequencies
    assert "ஒரு" not in analyze("தமிழ் ஒரு மொழி", opts).frequencies
    assert "ഒരു" not in analyze("കൊച്ചി ഒരു നഗരം", opts).frequencies
    assert "ഞാൻ" not in analyze("ഞാന്‍ വന്നു", opts).frequencies  # old-style chillu too


def test_filters_do_not_change_totals():
    text = "the cat and the hat"
    assert analyze(text, Options(remove_stopwords=True)).word_count == 5


def test_min_word_length():
    r = analyze("a an ant ants", Options(min_word_length=3))
    assert set(r.frequencies) == {"ant", "ants"}


# -- edge cases -------------------------------------------------------------------
@pytest.mark.parametrize("text", ["", "   \n\n ", "!!! ... ???", "।।"])
def test_empty_or_punctuation_only(text):
    r = analyze(text)
    assert r.word_count == 0 and r.sentences == []
    s = r.summary()
    assert s["Words"] == 0 and s["Most frequent word"] == "—"
    assert r.frequency_df().empty and r.bigram_df().empty


def test_paragraphs_and_crlf():
    assert len(analyze("one.\r\n\r\ntwo.\r\n\r\nthree.").paragraphs) == 3


# -- decoding ---------------------------------------------------------------------
def test_decode_utf8_with_bom_and_utf16():
    text = "தமிழ் मलयालम"
    assert decode_bytes(text.encode("utf-8-sig"))[0] == text
    assert decode_bytes(text.encode("utf-16"))[0] == text
    assert decode_bytes(text.encode("utf-8"))[1] == "utf-8-sig"


# -- comparison & export ------------------------------------------------------------
def test_compare_identical_and_disjoint():
    a = analyze("cat dog cat")
    assert compare(a, a)["jaccard"] == 1.0 and compare(a, a)["cosine"] == 1.0
    c = compare(a, analyze("தமிழ் மொழி"))
    assert c["jaccard"] == 0.0 and c["shared"] == 0


def test_csv_roundtrip_keeps_indic_text():
    r = analyze((SAMPLES / "malayalam.txt").read_text(encoding="utf-8"))
    data = to_csv_bytes(r.frequency_df(), index=True)
    assert data.startswith(b"\xef\xbb\xbf")  # BOM for Excel
    back = pd.read_csv(io.BytesIO(data), encoding="utf-8-sig")
    assert back.loc[0, "Word"] == "മലയാളം"
