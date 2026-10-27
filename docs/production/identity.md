# Local identity and review attribution

The default remains the supervised localhost bootstrap session for compatibility. Everyone with access to that page shares its session authority and can supply an alias; it must not be represented as independent multi-user identity.

An opt-in `AMI_PILOT_IDENTITY_FILE` now selects a startup-validated list of stable aliases, roles and SHA-256 token digests. Configured mode refuses malformed/duplicate identities or digests, unknown roles and plaintext-token fields. It does not fall back to bootstrap if loading fails. The public page contains no accepted token; the reviewer enters their individual token, which stays in page memory and is not placed in URLs or browser storage. Reloading requires reconnection. The existing `X-Pilot-Token` header is retained.

| Role | Read tasks and sources | Create/edit/retry/cancel | Review exact revision | Export approved revision |
|---|---|---|---|---|
| reader | Yes | No | No | No |
| analyst | Yes | Yes | No | Yes |
| reviewer | Yes | No | Yes | Yes |
| operator | Yes | Yes | Yes | Yes |

This is one shared public-data workspace, not per-document tenancy. Unknown API actions deny by default. The review alias must exactly equal the authenticated identity; attempts to impersonate another alias are rejected before a review is saved. The identity is persisted in the existing decision payload within its original transaction. Authorized action attempts also record identity/role/action in the existing event stream; these are labeled attempts, not inferred successful actions. No tokens/digests enter these events. Existing review/export rules, schemas and cached export bytes are unchanged.

## Operator setup

Do this explicitly in a private local directory; the agent has not generated real reviewer credentials or sent any invitations:

```powershell
.\.venv-release-check\Scripts\python.exe -m scripts.provision_pilot_identity --output .pilot-work/private-identities --principal sirapop=operator --principal reviewer-1=reviewer
$env:AMI_PILOT_IDENTITY_FILE=(Resolve-Path .pilot-work/private-identities/identities.json).Path
.\.venv-release-check\Scripts\python.exe -m src.pilot.launch
```

The helper saves random 32-byte bearer credentials in `private-tokens.json`, separately from the digest-only configuration, and prints paths only. It refuses an existing directory rather than overwriting credentials. Protect both files with operator-only filesystem access; on Windows verify NTFS ACLs because POSIX mode bits do not establish that boundary. Never commit or bake these files into an image. Give each reviewer only their own credential through an owner-chosen private channel. No automatic contact is included.

For a local container, mount only the digest configuration read-only and set its container path explicitly. The default Compose configuration does not enable this mode or mount operator secrets automatically. Restart the single application after rotating/revoking config entries; the loaded list is deliberately immutable for a running session. Sessions using a removed token are rejected after restart, including already-open pages.

## Qualification limits

These controls have synthetic offline authorization/attribution tests; actual independent reviewer sessions and target-deployment identity remain pending. This is not federated login, MFA, a secret vault, public internet authentication, or proof that credential custody is secure. Keep the existing localhost host/origin boundary. External hosting needs the named target's TLS, identity/access integration, token custody/rotation policy, access reviews and residual-risk acceptance before rollout. No sensitive customer/KYC/payment data is authorized. Historical shared-alias decisions remain historical; this mode does not retroactively authenticate them.
