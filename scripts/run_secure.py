"""Interactive local launcher. Prompts do not echo or write keys to disk."""

import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["smoke", "live"], default="smoke")
    parser.add_argument("--config", default=str(ROOT / "demo.local.json"))
    args = parser.parse_args()
    if not sys.stdin.isatty():
        raise SystemExit("Run from your own interactive terminal. Do not pipe credentials.")
    if not Path(args.config).exists():
        raise SystemExit("Copy demo.example.json to demo.local.json and set the op:// reference first.")
    warnings.simplefilter("error", getpass.GetPassWarning)
    env = {k: os.environ[k] for k in ("HOME", "PATH", "TMPDIR", "LANG") if k in os.environ}
    try:
        token = getpass.getpass("Scoped 1Password service-account token (hidden): ")
        if not token:
            raise SystemExit("No token entered.")
        env["OP_SERVICE_ACCOUNT_TOKEN"] = token
        command = [sys.executable, str(ROOT / "agent.py"), "--config", args.config, "--mode", args.mode]
        if args.mode == "live":
            print("This sends ONLY the configured synthetic PR content to OpenAI. Review the config first. The local $1 reservation ledger is cumulative; do not reset it to bypass the budget.")
            if input("Type SYNTHETIC to confirm this repository contains only approved demo data: ") != "SYNTHETIC":
                raise SystemExit("Cancelled.")
            env["OPENAI_API_KEY"] = getpass.getpass("OpenAI API key (hidden): ")
            if not env["OPENAI_API_KEY"]:
                raise SystemExit("No key entered.")
            command.append("--approve-model-call")
        result = subprocess.run(command, cwd=ROOT, env=env)
        return result.returncode
    finally:
        env.clear()  # No claim of guaranteed memory erasure in Python.


if __name__ == "__main__":
    raise SystemExit(main())
