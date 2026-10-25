"""BharatText — Indian language text analyzer."""

from .analyzer import (
    Analysis,
    Options,
    analyze,
    compare,
    comparison_table,
    decode_bytes,
    shared_words_df,
    to_csv_bytes,
    tokenize,
)

__all__ = [
    "Analysis",
    "Options",
    "analyze",
    "compare",
    "comparison_table",
    "decode_bytes",
    "shared_words_df",
    "to_csv_bytes",
    "tokenize",
]
__version__ = "1.0.0"
