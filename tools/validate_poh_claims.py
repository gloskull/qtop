#!/usr/bin/env python3
##
## qtop is a tool to monitor queuing systems - https://github.com/qtop/qtop
##
## Copyright (c) 2026 qtop contributors
##
## SPDX-License-Identifier: MIT
##
"""Validate the dependency-free, JSON-compatible YAML PoH claim registry."""

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "poh" / "claims.yaml"
PROVIDERS = set(["github", "gitlab", "keyoxide", "linkedin", "matrix", "orcid", "website"])
STATUSES = set(["candidate", "verified", "revoked"])
FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/]{20,}={0,2}$")
GITHUB_ACCOUNT_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


def fail(errors, message):
    errors.append(message)


def validate_participant(entry, index, errors):
    where = "participants[%d]" % index
    if not isinstance(entry, dict):
        fail(errors, "%s must be an object" % where)
        return

    github = entry.get("github")
    if not isinstance(github, str) or not GITHUB_ACCOUNT_RE.match(github):
        fail(errors, "%s.github must be a valid GitHub account name" % where)

    if entry.get("status") not in STATUSES:
        fail(errors, "%s.status must be candidate, verified, or revoked" % where)

    signing = entry.get("commit_signing")
    if not isinstance(signing, dict) or set(signing).difference(set(["fingerprints"])):
        fail(errors, "%s.commit_signing may contain only fingerprints" % where)
    else:
        fingerprints = signing.get("fingerprints", [])
        if not isinstance(fingerprints, list) or not all(isinstance(item, str) and FINGERPRINT_RE.match(item) for item in fingerprints):
            fail(errors, "%s.commit_signing.fingerprints must be SHA256 fingerprints" % where)

    claims = entry.get("claims")
    if not isinstance(claims, list) or not 1 <= len(claims) <= 5:
        fail(errors, "%s.claims must contain one to five claims" % where)
        return
    providers = set()
    github_url = None
    for claim_index, claim in enumerate(claims):
        claim_where = "%s.claims[%d]" % (where, claim_index)
        if not isinstance(claim, dict) or set(claim) != set(["provider", "url"]):
            fail(errors, "%s must contain only provider and url" % claim_where)
            continue
        provider = claim.get("provider")
        url = claim.get("url")
        if provider not in PROVIDERS:
            fail(errors, "%s.provider is not supported" % claim_where)
        elif provider in providers:
            fail(errors, "%s.provider duplicates %s" % (claim_where, provider))
        providers.add(provider)
        if not isinstance(url, str) or not url.startswith("https://"):
            fail(errors, "%s.url must be an HTTPS URL" % claim_where)
        if provider == "github":
            github_url = url
    expected_url = "https://github.com/%s" % github
    if github_url != expected_url:
        fail(errors, "%s must include github claim %s" % (where, expected_url))


def validate_registry(registry):
    errors = []
    if not isinstance(registry, dict) or set(registry) != set(["schema_version", "participants"]):
        return ["registry must contain only schema_version and participants"]
    if registry.get("schema_version") != 1:
        fail(errors, "schema_version must be 1")
    participants = registry.get("participants")
    if not isinstance(participants, list):
        return errors + ["participants must be a list"]
    accounts = set()
    for index, participant in enumerate(participants):
        validate_participant(participant, index, errors)
        if isinstance(participant, dict) and isinstance(participant.get("github"), str):
            account = participant["github"].lower()
            if account in accounts:
                fail(errors, "participants[%d].github duplicates an existing account" % index)
            accounts.add(account)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", nargs="?", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv)
    try:
        with args.registry.open(encoding="utf-8") as handle:
            registry = json.load(handle)
    except (OSError, ValueError) as exc:
        print("invalid PoH registry: %s" % exc, file=sys.stderr)
        return 1
    errors = validate_registry(registry)
    if errors:
        for error in errors:
            print("invalid PoH registry: %s" % error, file=sys.stderr)
        return 1
    print("PoH registry is valid: %s participant(s)" % len(registry["participants"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
