
def chunk_text(
    text: str,
    target_size: int = 1200,
    min_chars: int = 300
) -> list[str]:
    """
    Paragraph-aware chunking with size consistency and proper context
    """

    paragraphs = [
        p.strip()
        for p in text.split("\n")
        if len(p.strip()) > 50
    ]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # Ensure proper spacing between paragraphs
        separator = " " if current_chunk else ""
        
        if len(current_chunk) + len(separator) + len(para) <= target_size:
            current_chunk += separator + para
        else:
            # Save current chunk if it meets minimum size
            if len(current_chunk.strip()) >= min_chars:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                # If current chunk is too small, keep adding
                current_chunk += separator + para

    # Add last chunk if valid
    if len(current_chunk.strip()) >= min_chars:
        chunks.append(current_chunk.strip())

    return chunks
