"""Install only the official pinned release, after SHA-256 verification."""

import hashlib
import io
import os
import platform
import tarfile
import urllib.request
from pathlib import Path

VERSION = "2.0.3"
ASSETS = {
    ("Darwin", "arm64"): ("Darwin_arm64", "5c95c01f75a7ec2370607e989b2968d314b02a54d78af8a9fdf38f3dfe6135f4"),
    ("Darwin", "x86_64"): ("Darwin_x86_64", "115350858c3287843274efbf45e821d98f15d3304cb2c074740461ed32b45598"),
    ("Linux", "aarch64"): ("Linux_arm64", "5d2ddc71273fec8917e8f42cf19f26a6bd7acbb679b3a57de2917018b2eadf82"),
    ("Linux", "x86_64"): ("Linux_x86_64", "f797c20fe02a755865d0e2d46184ab47e31bf1619b0855b8d89c531e45a651c2"),
}


def main():
    key = (platform.system(), platform.machine())
    if key not in ASSETS:
        raise SystemExit("Platform not supported by this installer.")
    asset, checksum = ASSETS[key]
    url = f"https://github.com/github/github-mcp-server/releases/download/v{VERSION}/github-mcp-server_{asset}.tar.gz"
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = response.read(60000000)
    if hashlib.sha256(archive).hexdigest() != checksum:
        raise SystemExit("Checksum mismatch. Nothing installed.")
    dest = Path(__file__).resolve().parents[1] / "vendor"
    dest.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for name in ("github-mcp-server", "LICENSE"):
            member = tar.getmember(name)
            if not member.isfile():
                raise SystemExit("Unexpected archive entry.")
            stream = tar.extractfile(member)
            if stream is None:
                raise SystemExit("Missing archive file.")
            (dest / name).write_bytes(stream.read())
    os.chmod(dest / "github-mcp-server", 0o755)
    print(f"Verified official GitHub MCP {VERSION}; installed in vendor/.")


if __name__ == "__main__":
    main()
