"""Command-line interface.

    python -m bharattext samples/hindi.txt
    python -m bharattext samples/tamil.txt --top 15 --stopwords --csv reports/
"""

import argparse
import sys
from pathlib import Path

from .analyzer import Options, analyze, decode_bytes, to_csv_bytes


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="bharattext", description="Analyze text in Indian languages.")
    p.add_argument("file", help="UTF-8 .txt file, or '-' to read stdin")
    p.add_argument("--top", type=int, default=10, help="how many frequent words to show")
    p.add_argument("--stopwords", action="store_true", help="remove common function words")
    p.add_argument("--keep-numbers", action="store_true", help="count numbers as words in frequency")
    p.add_argument("--min-len", type=int, default=1, help="minimum word length (graphemes) for frequency")
    p.add_argument("--csv", metavar="DIR", help="write summary.csv and frequency.csv to DIR")
    args = p.parse_args(argv)

    if args.file == "-":
        text = sys.stdin.read()
    else:
        path = Path(args.file)
        if not path.is_file():
            p.error(f"file not found: {path}")
        text, enc = decode_bytes(path.read_bytes())
        if "fallback" in enc:
            print(f"warning: file is not UTF-8/UTF-16; decoded as {enc}", file=sys.stderr)

    opts = Options(
        remove_stopwords=args.stopwords,
        exclude_numbers=not args.keep_numbers,
        min_word_length=args.min_len,
        top_n=args.top,
    )
    result = analyze(text, opts)
    if not result.words:
        print("No words found — the input is empty or contains no letters.")
        return 1

    print("\n== Summary ==")
    for k, v in result.summary().items():
        print(f"  {k:<36} {v}")
    print(f"\n== Top {args.top} words ==")
    print(result.frequency_df().to_string())

    if args.csv:
        out = Path(args.csv)
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.csv").write_bytes(to_csv_bytes(result.summary_df()))
        (out / "frequency.csv").write_bytes(to_csv_bytes(result.frequency_df(n=len(result.frequencies)), index=True))
        print(f"\nCSV reports written to {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
