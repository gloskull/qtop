# Proof-of-humanity registry proof of concept

This directory is a deliberately small proof of concept for a future
`qtop/PoH` registry.  Its only tracked state is a public, reviewable list of
claims.  It does **not** collect identity documents, telephone numbers, postal
addresses, challenge answers, or email addresses.

`claims.yaml` uses the JSON-compatible YAML subset.  JSON is valid YAML, and
that subset lets the validator use Python's standard library rather than add a
runtime dependency.  A dedicated PoH repository can copy this directory
unchanged and enable `python3 tools/validate_poh_claims.py` in its CI.

## Candidate entry

Each participant has one GitHub account, a list of one to five public profile
claims, and a status.  Profile URLs are evidence links, not proof on their own.
Use only profiles that the participant has chosen to make public:

```yaml
{
  "schema_version": 1,
  "participants": [
    {
      "github": "octo-contributor",
      "commit_signing": {"fingerprints": ["SHA256:base64-public-key-fingerprint"]},
      "claims": [
        {"provider": "github", "url": "https://github.com/octo-contributor"},
        {"provider": "orcid", "url": "https://orcid.org/0000-0000-0000-0000"},
        {"provider": "keyoxide", "url": "https://keyoxide.org/example"}
      ],
      "status": "candidate"
    }
  ]
}
```

The permitted providers are `github`, `gitlab`, `keyoxide`, `linkedin`,
`matrix`, `orcid`, and `website`.  A provider may occur only once for a
participant.  The validator requires the GitHub claim to name the same account
as `github`; it also bounds each entry to five claims.  Fingerprints are
optional during the proof of concept, but when supplied they must use Git's
`SHA256:` fingerprint form.

## Lightweight review round

1. A contributor opens a PR that adds their candidate entry and has a
   cryptographically signed HEAD commit.  CI runs `git verify-commit HEAD` and
   `tools/validate_poh_claims.py`; a signature alone is not a human verdict.
2. A maintainer checks that the public claims are coherent, then sends a
   one-time nonce to the signed commit's author email (or another mutually
   agreed private channel).  The nonce and response stay out of Git and CI
   logs.
3. The contributor returns the requested response through that private
   channel and can explain the entry and their contribution.  A maintainer
   records only the resulting `verified` status in a reviewed, signed commit.
4. The maintainer may merge after ordinary code review.  `revoked` preserves a
   minimal, auditable outcome if a claim later becomes unreliable.

This creates a small cost for mass-created identities while leaving people free
to use the public account/profile combinations that work for them.  It is not a
biometric identity system and must not be used as the sole basis for trust or
access decisions.  Maintainers should offer an accessible alternative private
channel where email is unsuitable.

## Local checks

```sh
python3 tools/validate_poh_claims.py
git verify-commit HEAD
```

The first command validates schema and privacy-oriented structural rules.  The
second command verifies the Git signature locally; whether a key is trusted is
an explicit maintainer policy decision.
