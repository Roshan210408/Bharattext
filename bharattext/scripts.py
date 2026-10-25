"""Unicode script detection for Indian-language text.

Each Indic script occupies its own Unicode block, so the script of a letter
can be found from its code point alone. Language is *not* the same as script
(Hindi, Marathi and Nepali all use Devanagari), so labels say both.
"""

from collections import Counter

# (start, end, script name, typical languages)
SCRIPT_RANGES = [
    (0x0900, 0x097F, "Devanagari", "Hindi / Marathi / Nepali / Sanskrit"),
    (0x0980, 0x09FF, "Bengali", "Bengali / Assamese"),
    (0x0A00, 0x0A7F, "Gurmukhi", "Punjabi"),
    (0x0A80, 0x0AFF, "Gujarati", "Gujarati"),
    (0x0B00, 0x0B7F, "Odia", "Odia"),
    (0x0B80, 0x0BFF, "Tamil", "Tamil"),
    (0x0C00, 0x0C7F, "Telugu", "Telugu"),
    (0x0C80, 0x0CFF, "Kannada", "Kannada"),
    (0x0D00, 0x0D7F, "Malayalam", "Malayalam"),
    (0x0600, 0x06FF, "Arabic", "Urdu / Kashmiri / Sindhi"),
    (0xA8E0, 0xA8FF, "Devanagari", "Hindi / Marathi / Nepali / Sanskrit"),  # Devanagari Extended
    (0x1CD0, 0x1CFF, "Devanagari", "Hindi / Marathi / Nepali / Sanskrit"),  # Vedic Extensions
]

LANGUAGE_OF = {name: langs for _, _, name, langs in SCRIPT_RANGES}
LANGUAGE_OF["Latin"] = "English / other Latin-script"


def script_of(ch: str) -> str | None:
    """Return the script name of a single letter or mark, or None."""
    cp = ord(ch)
    if (0x41 <= cp <= 0x5A) or (0x61 <= cp <= 0x7A) or (0xC0 <= cp <= 0x24F):
        return "Latin"
    for start, end, name, _ in SCRIPT_RANGES:
        if start <= cp <= end:
            return name
    if ch.isalpha():
        return "Other"
    return None


def script_breakdown(text: str) -> Counter:
    """Count script-bearing characters (letters, vowel signs, viramas) per script."""
    counts = Counter()
    for ch in text:
        name = script_of(ch)
        if name:
            counts[name] += 1
    return counts


def dominant_script(text: str) -> str | None:
    counts = script_breakdown(text)
    return counts.most_common(1)[0][0] if counts else None
