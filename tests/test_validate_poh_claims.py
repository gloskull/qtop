import json
import subprocess
import sys

from tools.validate_poh_claims import validate_registry


def participant(account="octo-contributor"):
    return {
        "github": account,
        "commit_signing": {"fingerprints": ["SHA256:abcdefghijabcdefghijabcdefghijabcdefghijk="]},
        "claims": [
            {"provider": "github", "url": "https://github.com/%s" % account},
            {"provider": "orcid", "url": "https://orcid.org/0000-0000-0000-0000"},
        ],
        "status": "candidate",
    }


def registry(entries):
    return {"schema_version": 1, "participants": entries}


def test_validate_registry_accepts_a_bounded_public_claim_set():
    assert validate_registry(registry([participant()])) == []


def test_validate_registry_rejects_duplicate_provider_and_github_mismatch():
    entry = participant()
    entry["claims"].append({"provider": "orcid", "url": "https://orcid.org/other"})
    entry["claims"][0]["url"] = "https://github.com/someone-else"

    errors = validate_registry(registry([entry]))

    assert any("duplicates orcid" in error for error in errors)
    assert any("must include github claim" in error for error in errors)


def test_command_rejects_non_https_claim_url(tmp_path):
    entry = participant()
    entry["claims"][1]["url"] = "http://orcid.org/0000-0000-0000-0000"
    path = tmp_path / "claims.yaml"
    path.write_text(json.dumps(registry([entry])), encoding="utf-8")

    result = subprocess.run([sys.executable, "tools/validate_poh_claims.py", str(path)], capture_output=True, text=True)

    assert result.returncode == 1
    assert "must be an HTTPS URL" in result.stderr
