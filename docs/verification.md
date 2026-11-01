# Verification ledger

Initial build: 2026-10-31. All data is synthetic.

## Verified locally

- 30 offline tests passed on Python 3.12.14: fixed target/read-only application policy, rejection of broadened tool inventory, credential separation, bounded results, safe failures, and explicitly scripted rehearsal.
- Official GitHub MCP 2.0.3 downloaded from its release. Darwin arm64 archive SHA-256 matched `5c95c01f75a7ec2370607e989b2968d314b02a54d78af8a9fdf38f3dfe6135f4`.
- Real binary initialized through MCP Python 2.3.0 with a dummy invalid token; `tools/list` exposed exactly `pull_request_read` and confirmed the `get`/`get_diff` arguments. No GitHub tool calls or model calls in that protocol check.
- Installed 1Password CLI 2.40.0 exposes `op run` with `op://` references, not the newer `--environment` flag.
- Missing service-account configuration stops the smoke mode with a clear safe error.

## Not yet verified

- Valid 1Password service-account authentication or retrieval of a scoped GitHub PAT.
- Real GitHub PR reads through the credential-loaded MCP process.
- A real OpenAI model selecting tools and producing a grounded brief.
- Rotation, issuer revocation, or successful recovery with a replacement token.
- Container/cloud deployment, performance benefit, or arbitrary-agent isolation.

The protocol and fixture checks do not substitute for any of those live checks. Keep the words "offline fixture" visible if recording offline output. The separate invalid-format startup check is not a test of a once-valid service account being revoked.
