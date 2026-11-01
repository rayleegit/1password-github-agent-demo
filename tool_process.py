"""Runs after op resolves the reference. Scrub the child environment before exec."""

import os
import re
import sys


def github_env(source):
    token = source.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not re.fullmatch(r"github_pat_[A-Za-z0-9_]{20,}", token):
        raise ValueError("Use a resolved fine-grained GitHub PAT for this demo.")
    keep = {key: source[key] for key in ("PATH", "HOME", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "LANG") if key in source}
    keep["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
    # In particular: NO OP_SERVICE_ACCOUNT_TOKEN, OPENAI_API_KEY, proxy,
    # config override, OAuth client, command logging, or extra tool settings.
    return keep


def main():
    if len(sys.argv) != 2:
        return 2
    try:
        env = github_env(os.environ)
    except ValueError:
        print("Resolved fine-grained credential required.", file=sys.stderr)
        return 2
    binary = sys.argv[1]
    os.execve(binary, [binary, "stdio", "--read-only", "--tools=pull_request_read"], env)


if __name__ == "__main__":
    raise SystemExit(main())
