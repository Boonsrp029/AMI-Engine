"""Offline audit helper; reconstruct pinned GGUF Llama3 BPE, never query a model.

Pretokenizer reference: meta-llama/llama3, llama/tokenizer.py (Tokenizer.pat_str).
Metadata must come from the separately hash-pinned local model show snapshot.
Counts exclude Ollama chat-template and any server-added schema/instructions.
"""
PATTERN = r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"


def encoding(metadata):
    import tiktoken
    if metadata.get("tokenizer.ggml.pre") != "llama-bpe":
        raise ValueError("Unsupported tokenizer preprocessor")
    values = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
    symbols = values[:]
    extra = 0
    for value in range(256):
        if value not in values:
            values.append(value)
            symbols.append(256 + extra)
            extra += 1
    reverse = {chr(symbol): value for value, symbol in zip(values, symbols)}
    vocab, types = metadata["tokenizer.ggml.tokens"], metadata["tokenizer.ggml.token_type"]
    if len(vocab) != 128256 or len(types) != len(vocab) or set(types) != {1, 3}:
        raise ValueError("Unexpected pinned tokenizer vocabulary")
    ranks = {bytes(reverse[c] for c in token): i
             for i, (token, kind) in enumerate(zip(vocab, types)) if kind == 1}
    special = {token: i for i, (token, kind) in enumerate(zip(vocab, types)) if kind == 3}
    return tiktoken.Encoding(name="pinned-gguf-llama3", pat_str=PATTERN,
                             mergeable_ranks=ranks, special_tokens=special)
