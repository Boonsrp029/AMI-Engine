"""Local inference admission using hash-pinned tokenizer and model identity."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json


@dataclass(frozen=True)
class BoundedTransport:
    transport: object
    model_snapshot: dict
    tokenizer_path: str
    tokenizer_sha256: str

    def __call__(self, stage, schema, instruction, inputs):
        from src.pilot._model_identity import verify_model
        from scripts._llama_token_count import encoding
        raw = Path(self.tokenizer_path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != self.tokenizer_sha256:
            raise ValueError("Tokenizer metadata identity changed")
        counter = encoding(json.loads(raw))
        tokens = (len(counter.encode(instruction)) + len(counter.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))))
            + 256 + 900)
        # Our concrete transport binds schema to Ollama's format field, not to
        # messages. Preserve the conservative schema reserve for other adapters.
        from .generation import OllamaStructuredTransport
        if type(self.transport) is not OllamaStructuredTransport:
            tokens += len(counter.encode(json.dumps(schema.model_json_schema())))
        if tokens > 4096:
            raise ValueError("Conservative context budget exceeded")
        verify_model(self.model_snapshot)
        response = self.transport(stage, schema, instruction, inputs)
        verify_model(self.model_snapshot)
        return response
