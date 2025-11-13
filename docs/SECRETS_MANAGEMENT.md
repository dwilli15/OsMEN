# Secrets Management Playbook

This guide defines how production secrets (API tokens, OAuth refresh tokens, admin passwords)
are provisioned and stored for OsMEN.

## Storage Sources
- **1Password (OsMEN/Production vault)** – primary source of truth for human-managed secrets.
- **AWS Secrets Manager (`/osmen/prod/*`)** – optional mirror for infrastructure automation.
- **Local deployment files** – `.env` and `.env.production` (never committed) plus git-ignored `secrets/` directory for short-lived OAuth tokens.

## Workflow
1. Generate credentials (LLM keys, Postgres, Redis, admin passwords) and save them in 1Password with owner + rotation date.
2. Mirror the values into `.env.production` (and `.env` for local) immediately before deployment.
3. For OAuth providers (Google, Microsoft), store refresh tokens inside `secrets/oauth/` (directory already ignored) and limit file permissions to `600`.
4. Run `python scripts/automation/validate_security.py` to ensure `.env`/`.env.production` exist and no placeholder values remain.
5. Rotate high-risk secrets before every merge point (48h cadence) and update the vault entry with timestamp + operator initials.

## Tools
- `scripts/security/hash_password.py` – generate bcrypt hashes for `WEB_ADMIN_PASSWORD_HASH`.
- `scripts/automation/validate_security.py` – validates placeholder secrets and file permissions.

## Policies
- Never store API keys or OAuth tokens inside tracked files (source control, docs, issue trackers).
- Restrict `secrets/` directory permissions (`chmod 700 secrets`), and use OS-level disk encryption on hosts running OsMEN.
- Only Beta (Infrastructure) operators can rotate shared secrets; record rotations in `3agent_chat.md` for visibility.
