"""Create local public-data pilot credentials without printing bearer secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets

from src.pilot._identity import Principal


def provision(destination, entries):
    records, tokens = [], {}
    for entry in entries:
        identity, role = entry.split("=", 1)
        token = secrets.token_urlsafe(32)
        record = Principal(identity=identity, role=role, token_sha256=hashlib.sha256(token.encode()).hexdigest())
        if identity in tokens:
            raise ValueError("Duplicate identity")
        tokens[identity] = token
        records.append(record.model_dump())
    if not 1 <= len(records) <= 20:
        raise ValueError("One to twenty principals required")
    destination = Path(destination)
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    for name, data in (("identities.json", records), ("private-tokens.json", tokens)):
        path = destination / name
        with path.open("x", encoding="utf-8") as output:
            output.write(json.dumps(data, indent=2) + "\n")
        path.chmod(0o600)
    return destination / "identities.json", destination / "private-tokens.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--principal", action="append", required=True, help="Stable alias=reader|analyst|reviewer|operator")
    args = parser.parse_args(argv)
    try:
        config, private = provision(args.output, args.principal)
    except (OSError, ValueError, TypeError):
        parser.error("Could not provision identities; validate aliases/roles and use a new private output directory")
    print(f"Identity configuration: {config}\nPrivate credentials saved locally: {private}\nNo tokens printed. Restrict directory access before use; Windows ACLs require operator verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
