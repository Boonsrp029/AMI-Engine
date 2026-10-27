"""Opt-in local principal tokens; no identity-provider or network side effects."""
import hashlib
import json
from pathlib import Path
import re
import secrets

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class Principal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    identity: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    role: Literal["reader", "analyst", "reviewer", "operator"]
    token_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def load_principals(path):
    if not path:
        return None  # Existing supervised bootstrap mode; not multi-user identity.
    try:
        raw = Path(path).read_bytes()
        if len(raw) > 20_000:
            raise ValueError()
        records = json.loads(raw)
        if not isinstance(records, list) or not 1 <= len(records) <= 20:
            raise ValueError()
        principals = tuple(Principal.model_validate(record) for record in records)
        if (len({p.identity for p in principals}) != len(principals)
                or len({p.token_sha256 for p in principals}) != len(principals)):
            raise ValueError()
        return principals
    except (OSError, ValueError, TypeError):
        # Do not echo file contents, validation inputs or token digests.
        raise ValueError("Invalid pilot identity configuration; startup refused") from None


def authenticate(token, principals):
    if not isinstance(token, str) or not 24 <= len(token) <= 256:
        return None
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    matches = [p for p in principals if secrets.compare_digest(digest, p.token_sha256)]
    return matches[0] if len(matches) == 1 else None


def allowed(role, method, path):
    if method == "GET" and (path in {"/api/session", "/api/runs"}
                            or re.fullmatch(r"/api/runs/[a-f0-9]{32}", path)):
        return True
    if method == "GET" and re.fullmatch(r"/api/runs/[a-f0-9]{32}/export", path):
        return role in {"analyst", "reviewer", "operator"}
    if method == "POST" and path == "/api/runs":
        return role in {"analyst", "operator"}
    if method == "POST" and re.fullmatch(r"/api/runs/[a-f0-9]{32}/review", path):
        return role in {"reviewer", "operator"}
    if ((method == "POST" and re.fullmatch(r"/api/runs/[a-f0-9]{32}/(?:retry|cancel)", path))
            or (method == "PUT" and re.fullmatch(r"/api/runs/[a-f0-9]{32}/draft", path))):
        return role in {"analyst", "operator"}
    return False
