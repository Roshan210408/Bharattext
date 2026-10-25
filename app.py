"""BharatText — Streamlit web interface.

Run with:  streamlit run app.py
"""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from bharattext import Options, analyze, compare, comparison_table, decode_bytes, shared_words_df, to_csv_bytes

SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLES = {
    "English": "english.txt",
    "Hindi (हिन्दी)": "hindi.txt",
    "Tamil (தமிழ்)": "tamil.txt",
    "Malayalam (മലയാളം)": "malayalam.txt",
    "Mixed / code-mixed": "mixed.txt",
}
ACCENT = "#E8772E"  # saffron
SECOND = "#138808"  # green

st.set_page_config(page_title="BharatText", page_icon="🇮🇳", layout="wide")


# ---------------------------------------------------------------- helpers
def load_sample(name: str) -> str:
    return (SAMPLES_DIR / SAMPLES[name]).read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def run_analysis(text: str, remove_sw: bool, excl_num: bool, min_len: int, top_n: int):
    return analyze(text, Options(remove_sw, excl_num, min_len, top_n))


def text_input(key: str, default_sample: str, height: int = 220) -> tuple[str, str]:
    """Paste / upload / sample selector. Returns (text, source label)."""
    source = st.radio("Input", ["Paste text", "Upload .txt", "Sample"], horizontal=True,
                      key=f"{key}_src", label_visibility="collapsed")
    if source == "Upload .txt":
        f = st.file_uploader("Upload a UTF-8 text file", type=["txt"], key=f"{key}_file")
        if f is None:
            return "", ""
        text, enc = decode_bytes(f.getvalue())
        if "fallback" in enc:
            st.warning("This file isn't UTF-8 or UTF-16, so Indian scripts may show as garbage. "
                       "Re-save it as UTF-8 and upload again.")
        return text, f.name
    if source == "Sample":
        name = st.selectbox("Sample", list(SAMPLES), index=list(SAMPLES).index(default_sample),
                            key=f"{key}_sample")
        text = load_sample(name)
        # Key includes the sample name: a keyed widget keeps its old value otherwise.
        st.text_area("Preview", text, height=height, disabled=True, key=f"{key}_preview_{name}")
        return text, name
    text = st.text_area("Type or paste text in any Indian language", height=height, key=f"{key}_text",
                        placeholder="ഇവിടെ ടൈപ്പ് ചെയ്യുക · यहाँ लिखें · இங்கே தட்டச்சு செய்யவும் · Type here")
    return text, "pasted text"


def bar_chart(df: pd.DataFrame, x: str, y: str, color: str = ACCENT, height: int | None = None):
    h = height or max(180, 30 * len(df))
    return (
        alt.Chart(df)
        .mark_bar(color=color, cornerRadiusEnd=3)
        .encode(
            x=alt.X(f"{x}:Q", title=x, axis=alt.Axis(tickMinStep=1)),
            y=alt.Y(f"{y}:N", sort="-x", title=None,
                    axis=alt.Axis(labelLimit=260, labelFontSize=13, labelOverlap=False)),
            tooltip=list(df.columns),
        )
        .properties(height=h)
    )


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⚙️ Options")
    remove_sw = st.toggle("Remove stopwords", value=True,
                          help="Drops common function words (the, है, ஒரு, ഒരു …) from frequency results.")
    excl_num = st.toggle("Ignore numbers", value=True, help="Leaves 2026, ३, ൩ etc. out of frequency results.")
    min_len = st.slider("Minimum word length (letters)", 1, 6, 1,
                        help="Measured in graphemes, so क्षि counts as one letter.")
    top_n = st.slider("Top words to show", 5, 50, 15)
    st.divider()
    st.caption("Filters affect word frequency, bigrams and comparison. "
               "Totals (words, sentences…) always count every word.")
    st.caption("Supported: English, Hindi, Tamil, Malayalam stopwords; script detection for "
               "Devanagari, Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam, Urdu.")

opts = (remove_sw, excl_num, min_len, top_n)

st.title("🇮🇳 BharatText")
st.markdown("Word, sentence and frequency analysis for text in Indian languages.")

tab_analyze, tab_compare = st.tabs(["📊 Analyze", "⚖️ Compare two texts"])

# ---------------------------------------------------------------- analyze
with tab_analyze:
    text, label = text_input("main", "Hindi (हिन्दी)")

    if not text.strip():
        st.info("Paste some text, upload a .txt file, or pick a sample to begin.")
    else:
        r = run_analysis(text, *opts)
        if not r.words:
            st.warning("No words found. The text contains only spaces, punctuation or symbols.")
        else:
            s = r.summary()
            st.markdown(f"**Detected script:** {s['Dominant script']} &nbsp;·&nbsp; "
                        f"likely {s['Likely language(s)']}")
            c = st.columns(5)
            c[0].metric("Words", f"{r.word_count:,}", border=True)
            c[1].metric("Unique words", f"{r.unique_words:,}", border=True)
            c[2].metric("Sentences", s["Sentences"], border=True)
            c[3].metric("Paragraphs", s["Paragraphs"], border=True)
            c[4].metric("Characters", f"{s['Characters (with spaces)']:,}", border=True)

            left, right = st.columns([3, 2], gap="large")
            with left:
                st.subheader(f"Top {top_n} words")
                freq = r.frequency_df()
                if freq.empty:
                    st.info("Every word was filtered out — loosen the options in the sidebar.")
                else:
                    st.altair_chart(bar_chart(freq.reset_index(), "Count", "Word"), width="stretch")
                    with st.expander("Frequency table"):
                        st.dataframe(freq, width="stretch")

            with right:
                st.subheader("Scripts used")
                sdf = r.script_df()
                st.altair_chart(
                    alt.Chart(sdf).mark_arc(innerRadius=55).encode(
                        theta="Characters:Q",
                        color=alt.Color("Script:N", legend=alt.Legend(orient="bottom")),
                        tooltip=["Script", "Characters", "Percent"],
                    ).properties(height=240),
                    width="stretch",
                )
                st.subheader("Word length")
                wl = r.word_length_df()
                st.altair_chart(
                    alt.Chart(wl).mark_bar(color=SECOND).encode(
                        x=alt.X("Length (graphemes):O", title="Letters per word"),
                        y=alt.Y("Words:Q"),
                        tooltip=list(wl.columns),
                    ).properties(height=200),
                    width="stretch",
                )

            b1, b2 = st.columns([2, 3], gap="large")
            with b1:
                st.subheader("Frequent word pairs")
                bg = r.bigram_df()
                if bg.empty:
                    st.caption("Not enough words.")
                else:
                    st.dataframe(bg, width="stretch")
            with b2:
                st.subheader("All statistics")
                st.dataframe(r.summary_df().astype({"Value": str}), hide_index=True, width="stretch", height=390)

            st.subheader("Download reports")
            stem = Path(label).stem.replace(" ", "_") or "text"
            d1, d2, d3 = st.columns(3)
            d1.download_button("⬇️ Summary (CSV)", to_csv_bytes(r.summary_df()),
                               f"{stem}_summary.csv", "text/csv")
            d2.download_button("⬇️ All word frequencies (CSV)",
                               to_csv_bytes(r.frequency_df(n=len(r.frequencies)), index=True),
                               f"{stem}_frequency.csv", "text/csv")
            d3.download_button("⬇️ Word pairs (CSV)", to_csv_bytes(r.bigram_df(50)),
                               f"{stem}_bigrams.csv", "text/csv")

# ---------------------------------------------------------------- compare
with tab_compare:
    ca, cb = st.columns(2, gap="large")
    with ca:
        st.markdown("**Text A**")
        text_a, label_a = text_input("a", "English", height=180)
    with cb:
        st.markdown("**Text B**")
        text_b, label_b = text_input("b", "Mixed / code-mixed", height=180)

    if not (text_a.strip() and text_b.strip()):
        st.info("Provide both texts to compare them.")
    else:
        ra, rb = run_analysis(text_a, *opts), run_analysis(text_b, *opts)
        cmp = compare(ra, rb)
        m = st.columns(5)
        m[0].metric("Vocabulary overlap", f"{cmp['jaccard']:.0%}", help="Jaccard: shared words ÷ all distinct words", border=True)
        m[1].metric("Frequency similarity", f"{cmp['cosine']:.0%}", help="Cosine similarity of word-count vectors", border=True)
        m[2].metric("Shared words", cmp["shared"], border=True)
        m[3].metric("Only in A", cmp["only_a"], border=True)
        m[4].metric("Only in B", cmp["only_b"], border=True)

        t1, t2 = st.columns([3, 2], gap="large")
        with t1:
            st.subheader("Side by side")
            table = comparison_table(ra, rb, "Text A", "Text B").astype(str)
            st.dataframe(table, hide_index=True, width="stretch", height=420)
            st.download_button("⬇️ Comparison (CSV)", to_csv_bytes(table), "comparison.csv", "text/csv")
        with t2:
            st.subheader("Words both texts use")
            shared = shared_words_df(ra, rb)
            if shared.empty:
                st.caption("No words in common — different languages usually share none.")
            else:
                long = shared.melt("Word", var_name="Text", value_name="Count")
                st.altair_chart(
                    alt.Chart(long).mark_bar().encode(
                        x=alt.X("Count:Q", axis=alt.Axis(tickMinStep=1)),
                        y=alt.Y("Word:N", sort="-x", title=None,
                                axis=alt.Axis(labelLimit=260, labelFontSize=13, labelOverlap=False)),
                        color=alt.Color("Text:N", scale=alt.Scale(range=[ACCENT, SECOND]),
                                        legend=alt.Legend(orient="bottom")),
                        yOffset="Text:N",
                        tooltip=["Word", "Text", "Count"],
                    ).properties(height=max(200, 34 * len(shared))),
                    width="stretch",
                )
