# Verification ledger

Initial build: 2026-10-31. All data is synthetic.

## Verified locally

- 30 offline tests passed on Python 3.12.14: fixed target/read-only application policy, rejection of broadened tool inventory, credential separation, bounded results, safe failures, and explicitly scripted rehearsal.
- Official GitHub MCP 2.0.3 downloaded from its release. Darwin arm64 archive SHA-256 matched `5c95c01f75a7ec2370607e989b2968d314b02a54d78af8a9fdf38f3dfe6135f4`.
- Real binary initialized through MCP Python 2.3.0 with a dummy invalid token; `tools/list` exposed exactly `pull_request_read` and confirmed the `get`/`get_diff` arguments. No GitHub tool calls or model calls in that protocol check.
- Installed 1Password CLI 2.40.0 exposes `op run` with `op://` references, not the newer `--environment` flag.
- Missing service-account configuration stops the smoke mode with a clear safe error.
- An invalid-placeholder `op run` startup check timed out after 15 seconds in the restricted local environment. This is **inconclusive**, not a successful denial or a revocation test. The check now reports that state without a traceback.
- After adding the local cumulative spending guard and hidden-input launcher, 36 tests pass on main (37 with the synthetic PR's extra boundary test). The cost guard rejects unreviewed models, oversized requests, corrupt ledgers, and cumulative reservations over $1.
- The configured model is now `gpt-6.1-terra`; the earlier GPT-5 Mini draft default was replaced after official documentation marked it deprecated. Pricing reviewed: standard $1/M input and $5/M output on 2026-10-31, https://developers.openai.com/api/docs/pricing. Account availability and actual provider requests are unverified.

## Not yet verified

- Valid 1Password service-account authentication or retrieval of a scoped GitHub PAT.
- Real GitHub PR reads through the credential-loaded MCP process.
- A real OpenAI model selecting tools and producing a grounded brief.
- Rotation, issuer revocation, or successful recovery with a replacement token.
- Container/cloud deployment, performance benefit, or arbitrary-agent isolation.

The protocol and fixture checks do not substitute for any of those live checks. Keep the words "offline fixture" visible if recording offline output. The separate invalid-format startup check is not a test of a once-valid service account being revoked.
