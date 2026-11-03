# Tests and verification

Updated 2 November 2026. The example uses synthetic PR content.

## Run the offline suite

```sh
python -m unittest discover -s tests -v
python agent.py --mode offline
```

The current main branch has 62 tests. They require Python 3.11+ but no external packages, credentials, or network calls. GitHub Actions runs the suite and the scripted fixture on pushes and pull requests. Check the result for the exact commit you use.

The suite covers:

- Fixed repository/PR identity, permitted read methods, tool inventory, and argument validation.
- Bounded content, duplicate-read rejection, and refusal to produce a brief before both required reads.
- GitHub response shape and metadata minimization.
- Best-effort GitHub, model-provider, and service-account credential-pattern detection, including rejection of recognizable token strings in tool results and final output.
- Credential separation between the parent, CLI, and GitHub MCP environment. Model-provider authentication stays in the API header rather than the request body.
- Diagnostic events that omit PR content and raw upstream errors. The final brief intentionally contains PR content.
- Safe failure categories, bounded HTTP 429 inspection, request-ID validation, and nested error handling.
- Cumulative spending reservations and interactive-launcher sequencing and cancellation.

The suite also passes with site packages disabled and socket connection attempts blocked. Mocked checks validate these contracts, not the behavior of a live service or every possible secret format.

## Live integration evidence

A 1 November terminal transcript records GitHub MCP 2.0.3 initialization, two successful reads of synthetic PR #1 (details and diff), three model responses, and a cited review brief. The brief is consistent with the PR diff and does not claim to execute tests.

This demonstrates a successful local integration, not an independent security audit or validation of subsequent patches. The public PR does not establish private-repository authorization or least-privilege token scopes. Tool durations are not end-to-end performance benchmarks.

## Version and startup checks

- The official GitHub MCP 2.0.3 Darwin arm64 release archive matched SHA-256 `5c95c01f75a7ec2370607e989b2968d314b02a54d78af8a9fdf38f3dfe6135f4`.
- The pinned server initialized through MCP Python 2.3.0 and exposed the expected single tool. A protocol handshake alone does not verify authenticated reads.
- 1Password CLI 2.40.0 supported the `op://` reference and `op run` path used here. This example does not depend on `--environment`.
- An invalid-placeholder startup probe timed out after 15 seconds. Its result is inconclusive, not evidence of successful denial.

## Not established by these tests

- Actual GitHub PAT and 1Password vault permissions.
- Live credential replacement, issuer revocation, recovery, or negative-access behavior.
- Container/cloud deployment or protection against unrestricted same-host processes.
- Complete prompt-injection resistance, comprehensive secret detection, or correctness of every generated brief.
- PR-review speed, developer productivity, or cost savings.

Offline mode is a scripted fixture. It is not an AI model response or authenticated GitHub evidence. No repository code is executed by the agent.
