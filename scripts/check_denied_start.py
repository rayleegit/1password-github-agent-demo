"""Test actual op startup with an invalid placeholder token, not real credentials."""

import json
import os
import shutil
import subprocess
import sys


def main():
    op = shutil.which("op")
    if not op:
        raise SystemExit("1Password CLI is not installed")
    env = {k: os.environ[k] for k in ("HOME", "PATH", "TMPDIR") if k in os.environ}
    env.update({"OP_SERVICE_ACCOUNT_TOKEN": "INVALID_TEST_TOKEN_NOT_A_CREDENTIAL", "OP_BIOMETRIC_UNLOCK_ENABLED": "false", "DEMO_SECRET": "op://nonexistent-demo-vault/nonexistent-demo-item/credential"})
    result = subprocess.run([op, "run", "--", sys.executable, "-c", 'print("CHILD_STARTED")'], env=env, capture_output=True, timeout=15)
    child_started = b"CHILD_STARTED" in result.stdout
    passed = result.returncode != 0 and not child_started
    print(json.dumps({"mode": "invalid-format-startup-test", "passed": passed, "exit_code": result.returncode, "child_started": child_started, "real_credentials_used": False, "model_calls": 0, "proves_live_revocation": False}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
