import re
import hashlib

# Optional lightweight noise phrases (kept minimal)

def clean_text(text: str) -> str:
    # 1. Fix common double-encoding issues (UTF-8 bytes interpreted as Windows-1252)
    # These appear as â€™ style artifacts
    try:
        # Try to detect if text has UTF-8 bytes misinterpreted as latin-1/cp1252
        if isinstance(text, str):
            # Encode as latin-1 and decode as utf-8 to fix double-encoding
            try:
                fixed_text = text.encode('latin-1').decode('utf-8')
                text = fixed_text
            except (UnicodeDecodeError, UnicodeEncodeError):
                # If that fails, use manual replacements
                pass
    except:
        pass
    
    # 2. Manual fixes for common mojibake patterns
    replacements = {
        # Common Windows-1252 to UTF-8 mojibake
        '\u00e2\u0080\u0099': "'",  # â€™ → '
        '\u00e2\u0080\u0098': "'",  # â€˜ → '
        '\u00e2\u0080\u009c': '"',  # â€œ → "
        '\u00e2\u0080\u009d': '"',  # â€ → "
        '\u00e2\u0080\u0094': '-',  # â€" → —
        '\u00e2\u0080\u0093': '-',  # â€" → –
        '\u00e2\u0080\u00a6': '...',  # â€¦ → …
        '\u00c2\u00a0': ' ',  # Â  → non-breaking space
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    
    # 3. Normalize unicode spaces
    text = text.replace("\xa0", " ")
    text = text.replace("\u00a0", " ")

    # 4. Remove known noise phrases


    # 5. Split into paragraphs
    paragraphs = [
        p.strip()
        for p in re.split(r"\n+", text)
        if len(p.strip()) > 50
    ]

    # 6. Deduplicate paragraphs using hashing
    seen = set()
    cleaned_paragraphs = []

    for p in paragraphs:
        key = hashlib.md5(p.lower().encode("utf-8")).hexdigest()
        if key not in seen:
            seen.add(key)
            cleaned_paragraphs.append(p)

    # 7. Normalize whitespace again
    cleaned_text = "\n".join(cleaned_paragraphs)
    cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text)

    return cleaned_text.strip()
