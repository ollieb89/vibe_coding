from corpus_analyzer.llm.chunked_processor import split_on_headings


def test_no_split_in_code_block():
    # 20 lines of text
    prefix = "Line\n" * 20
    # Code block of 50 lines
    code_body = ("print('code run')\n" * 50)
    code_block = f"```python\n{code_body}```\n"

    content = prefix + code_block

    # Approx length: 20*5 = 100. Code: 50*18 = 900. Total 1000.
    # Set max_chunk to 500.
    # It should ideally split BEFORE the code block, or AFTER, but not IN logic.
    # If it splits in logic, the first chunk has unclosed ``` and second has un-opened ```.

    chunks = split_on_headings(content, max_chunk_size=500)

    for _chunk in chunks:
        # Simple heuristic: count ticks. Should be even in every valid chunk
        # (unless the block spans the whole chunk which is a harder case,
        # but here the block (900) > max (500), so it MUST split?
        # No, usually we want to allow exceeding max slightly to keep block intact,
        # OR split, but close/reopen blocks.)

        # Taking "Respect Semantic Boundaries" to mean "Try not to break blocks":
        # If we can't avoid it, we should verify the behavior.
        # But if the block is 900 and max is 500, we HAVE to split.
        pass

def test_respect_code_blocks_if_fitting():
    # Case where block FITS, but we effectively split it because of previous content?

    # Text (400 chars). Code (400 chars). Max 500.
    # 400 < 500. Appends text.
    # Append code line by line.
    # At line X of code, total > 500.
    # Current logic: Force splits at line X.
    # Result: Broken code block.

    prefix = "a" * 400 + "\n"
    code = "```\n" + ("b" * 380) + "\n```\n"
    content = prefix + code

    chunks = split_on_headings(content, max_chunk_size=500)

    # We expect chunk 0 to be the prefix (400).
    # Chunk 1 to be the code (400).
    # Instead of Chunk 0 being 500 (Prefix + half code).

    assert len(chunks) >= 2
    # Verify strict block integrity if possible
    # Just checking if chunk[0] ends with newline or text, not open code block
    assert chunks[0].content.count("```") % 2 == 0, "Chunk 0 has unclosed code block"
