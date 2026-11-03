# Verification ledger

Updated 2 November 2026. All task content is synthetic. Offline checks and the recorded live-run transcript are distinguished below.

## Recorded live run — 1 November

The recorded terminal transcript contains:
- MCP server 2.0.3 initialized with exactly `pull_request_read`.
- Three `model_response_received` events.
- Two `tool_complete` events: details (484 ms) and diff (353 ms).
- `brief_ready` with three model requests and two tool calls.
- A cited brief for PR #1 identifying the 30-second retry cap, unchanged 0–20 integer validation, and assertions at attempts 5 and 20. It explicitly did not claim to execute tests.

The brief is consistent with the synthetic PR branch diff. The transcript supports successful local GitHub reads and the model/tool loop; it is not an independent security audit or verification of subsequent patches. It does not establish least-privilege settings: inspect the actual provider and vault permissions separately. Tool durations are not whole-run latency or performance benchmarks.

An earlier live attempt returned OpenAI HTTP 429. The supplied failure did not preserve the provider's precise quota/rate code; the later successful run does not establish which account setting or transient condition changed. Do not claim the diagnostic patch fixed billing.

## Current local verification

- 62 offline tests pass on the implementation branch based on main. Tests cover application/tool policy, spending guards, diagnostics, launcher behavior, and content boundaries. They use synthetic strings and mocked network/child processes; no credentials or paid services are needed. An earlier 63-test run also included the separate retry-cap test in demo PR #1, which intentionally remains unmerged.
- Added checks cover 1Password service-account token patterns in tool data and final output; exact PR metadata selection; null versus malformed descriptions; strict PR-number and text-block types; PR content in model requests but not diagnostic events; and the model-provider key in its authentication header rather than the request body.
- Before the small implementation patch, the expanded suite reproduced failures in token detection and metadata validation/minimization. The patch adds the `ops_` recognizer, removes unused `state` metadata, and validates description/identity/text types. This is additional defense, not evidence of a previously exploited leak.
- The offline suite also runs with site packages disabled, matching the dependency-free CI intent. The task-group regression uses Python's built-in ExceptionGroup behavior.
- The 2 November local run also passed with socket connection attempts patched to fail. The separate offline CLI rehearsal completed with its fixture label, and `git diff --check` was clean. These checks made no real API call, credential retrieval, or budget-ledger mutation.
- Safe diagnostics preserve fixed error categories, HTTP status, and validated request IDs, not raw keys, payloads, traceback text, or error messages. For 429 only, bounded in-memory JSON maps allowlisted codes/types to fixed guidance.
- The optional `--pause-before-run` launcher flag is tested with dummy values and a mocked child. It does not change permissions or the cumulative cost guard. No new live model call was made to test this UI change.
- Offline fixture mode remains labeled as scripted, not AI or live GitHub evidence.
- GitHub Actions runs the offline suite and fixture on pushes and pull requests. Check the workflow result for the exact commit being used; a prior green run does not validate later changes.

## Earlier foundation checks — 31 October

- Official GitHub MCP 2.0.3 release archive for Darwin arm64 matched SHA-256 `5c95c01f75a7ec2370607e989b2968d314b02a54d78af8a9fdf38f3dfe6135f4`.
- The real binary initialized via MCP Python 2.3.0 with a dummy invalid token; tools/list confirmed the single tool and get/get_diff arguments. That handshake alone made no authenticated GitHub or model call.
- Installed 1Password CLI 2.40.0 supported op:// with op run; the inspected help did not expose --environment, which this implementation does not use.
- The invalid-placeholder startup probe timed out after 15 seconds. This remains inconclusive, not evidence of successful denial or live revocation.
- Model/cost guard: gpt-6.1-terra, default tier; reviewed 31 October at $1/M input and $5/M output. The guard reserves conservatively at twice those rates and rejects unreviewed model changes. Reservations are not provider-billed charges. No ledger reset or added allowance was performed in this revision.

## Still unverified

- Actual least-privilege PAT and 1Password vault permissions, beyond the application's fixed target/tool constraints.
- Private-repository authorization: the example is public, so a successful read is not a private-access or permission-denial test.
- Denied access, successful credential replacement, issuer revocation, and recovery.
- Container/cloud deployment, performance benefits, or isolation from arbitrary shell access.
- Comprehensive prompt-injection resistance or correctness of every generated brief.

Use actual screen footage for live proof. Label a static result as a completed live run. Do not animate a transcript as fresh execution or show fixture output as live evidence.
