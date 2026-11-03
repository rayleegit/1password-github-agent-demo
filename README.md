# Runtime secret injection for a bounded PR-review agent

A bounded Python agent reads **one configured pull request** using GitHub's official MCP server. 1Password CLI resolves a secret reference at startup. The model receives PR text, not the GitHub credential as part of its messages.

**Status (2 November 2026):** a recorded local run on 1 November completed three model responses, two real PR reads, and a cited brief. Subsequent content-boundary and diagnostic changes have offline test coverage, not a new live run. See [verification](docs/verification.md) for evidence and limits. Denial, rotation/revocation and cloud deployment remain unverified. Offline mode is a scripted fixture, not an AI model or authenticated demonstration.

## What this teaches

1. Give the agent one useful, read-only job: summarize an existing PR's changes and suggest human-review questions. The example prompt requests three bullets and two questions; those counts are not a security feature.
2. Let a trusted tool process handle authentication. Keep the credential out of code and model messages.
3. Rotate a stored credential without changing the tool's application code or secret reference; start a fresh tool process to load the new value.
4. Keep the boundaries explicit: secret delivery is not a sandbox, GitHub authorization, or prompt-injection immunity.

```text
Scoped 1Password service account → op run → credential scrubber → GitHub MCP → GitHub
                                            ↑ tool calls / PR data ↓
                                      bounded Python agent → OpenAI Responses
```

The bootstrap service-account token is a secret too. It belongs in your deployment platform's protected secret configuration. The GitHub process receives only its fine-grained PAT, not the bootstrap or model-provider token. The trusted Python parent still has the bootstrap/provider tokens; this is process hygiene, NOT isolation from a hostile process on the same host.

## Follow the input, credential, and output

The demonstrated 1Password feature is **CLI `op run`**: resolve secret references and supply their values to a child process at startup. The service account authorizes that feature; GitHub MCP is the tool being launched. No modification of GitHub's server or replacement with a 1Password SDK is needed.

1. **Configure the task.** `demo.example.json` identifies an existing repository/PR and an `op://vault/item/field` locator. The locator names where the GitHub token is stored, not its value. Put your own settings in ignored `demo.local.json`.
2. **Authorize the launcher.** `scripts/run_secure.py` accepts the bootstrap and model-provider keys through hidden local prompts. It starts `agent.py`, which reads the configuration. Neither key is written to project files by the launcher.
3. **Start the tool.** `agent.py` passes the locator as `GITHUB_PERSONAL_ACCESS_TOKEN` to `op run -- <python> tool_process.py <github-mcp-binary>`. The CLI resolves it. The helper removes unrelated credentials, then starts the official GitHub MCP server with `--read-only --tools=pull_request_read`.
4. **Read the PR.** The model requests `details` or `diff`. Python validates that choice and supplies the fixed repository/PR. GitHub MCP authenticates to GitHub with the resolved PAT; selected title/description/URL or diff data returns to the model. This does not create a PR or execute its code.
5. **Produce a brief.** After both reads, the model writes the review aid. Diagnostic events omit PR text; the final brief intentionally contains PR information and needs the same care as that information.

| Credential | What it authorizes | Where this demo supplies it |
| --- | --- | --- |
| 1Password Service Account token | Reading the dedicated vault | Hidden launcher input → trusted parent → CLI. Removed from the final GitHub MCP environment. |
| GitHub fine-grained PAT | GitHub API reads, according to its actual permissions | Vault → `op run` → helper → GitHub MCP environment and its GitHub API authentication. |
| Model-provider key | Model API requests | Hidden launcher input → trusted parent → API authorization header. Not model messages or the GitHub MCP environment. |

The bootstrap token cannot be retrieved from that same vault before the CLI is authorized. The hidden prompt is a local demo choice, not a production secret store; use protected workload provisioning in production. Credentials still exist in process memory. Hidden input avoids terminal echo, not clipboard monitoring or compromise of the host.

### What improves over a plaintext `.env`?

The GitHub token is not saved in the repository's working files, so reading this configuration yields a locator rather than a usable GitHub token. Git ignore rules alone do not prevent a permitted shell or process from reading a local file. This reduces a saved-secret exposure path; the application's narrow tool interface separately limits what this agent can do.

The `.env` format itself is not the problem: it can hold `op://` references, and a correctly isolated application using a plaintext `.env` can also keep tokens out of model messages. `op run` is not a sandbox. A general agent with access to the credential-bearing process or an authorized CLI may still obtain secrets. See [1Password's process-environment warning](https://www.1password.dev/cli/secrets-environment-variables).

## Run without accounts or credits

Python 3.11+:

```sh
python -m unittest discover -s tests -v
python agent.py --mode offline
```

Offline mode uses no packages, credentials, network, or AI calls. It exercises the loop's schema, budgets, and two-view workflow with explicit fixture labels. CI runs only these tests and this rehearsal.

## Set up the real integration

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
.venv/bin/python scripts/install_mcp.py
cp demo.example.json demo.local.json
```

The installer downloads GitHub MCP **2.0.3** from the official GitHub release and verifies a platform-specific SHA-256 before extracting the binary. macOS and Linux are supported. The CLI has been inspected on macOS with 1Password **2.40.0**. This version supports `op://` references; its local help does not expose `op run --environment`, so this demo does not depend on that newer flag.

### Credentials: configure outside chat and recording

- Create a short-lived fine-grained GitHub PAT for the selected **synthetic demo repository**. Grant Pull requests: Read-only and the required automatic Metadata permission. Do not use a broad classic PAT. Verify the exact scopes against the PR endpoint. This example repository is public: successfully reading it does not prove access to a private repository or prove that the token lacks write permissions. The application also hard-binds owner/repo/PR: a fine-grained PAT can still read public resources outside its selected private repositories.
- Store the PAT in a dedicated 1Password vault/item. Update `secret_ref` in `demo.local.json` with its `op://vault/item/field` reference. Prefer item/field IDs for rename resilience. No token belongs in the JSON.
- Create a service account with read access only to that dedicated vault. Supply `OP_SERVICE_ACCOUNT_TOKEN` through a protected runtime secret or an ephemeral, non-echoing local prompt. Do not commit it, put it in shell history, paste it into chat, or show it on screen.
- Set `OPENAI_API_KEY` separately for the model call. The default is `gpt-6.1-terra`, a current Responses tool-calling model; account access still requires verification. The spending guard rejects unreviewed model/tier changes.
- Inspect the synthetic PR before consenting to send it to OpenAI. `store:false` avoids application-response storage; it is not a blanket zero-data-retention guarantee. Review your provider's retention controls and terms.

Do not reuse the GitHub CLI's broad account credential as the agent token. No credential creation, rotation, revocation, or billing change is automated here.

### Smoke test (real GitHub, no model)

```sh
.venv/bin/python agent.py --config demo.local.json --mode smoke
```

This starts `op run`, scrubs the child environment, launches the pinned official MCP server with `--read-only --tools=pull_request_read`, verifies the actual tool inventory, and reads details and diff. It prints metadata-only status. A successful smoke test is not an AI-agent run.

### Real AI agent

```sh
.venv/bin/python agent.py --config demo.local.json --mode live --approve-model-call
```

The approval flag is an explicit operator check. Maximum four model requests, three tool calls, 900 output tokens per request, and bounded tool content. A cumulative local $1 reservation ledger in `artifacts/model-budget.json` reserves before each HTTP request at twice the reviewed token rates, using a conservative input bound and no retry refunds. This is not a provider-enforced billing cap or a guarantee against future pricing changes. Recheck pricing before live use, keep the ledger across runs, and configure provider billing controls too. Live requests send the approved synthetic PR and instructions only. No implicit retries. On a tool failure, the run ends without a fabricated brief.

For local manual entry without echo or shell-history exposure:

```sh
.venv/bin/python scripts/run_secure.py --mode smoke
# After the smoke test succeeds and the synthetic data/API budget are approved:
.venv/bin/python scripts/run_secure.py --mode live
```

The launcher prompts for the bootstrap/provider keys locally and never writes them to a file. The GitHub PAT stays in 1Password. Do not type secrets while screen recording. Process memory still contains credentials; this is not memory isolation.

For capture, add `--pause-before-run`. It pauses after hidden credential entry and consent, before starting the child process. Close credential UI, frame the terminal, start recording, then press Enter; Ctrl-C cancels. This changes only recording timing, not permissions, token handling, or the cumulative spending guard. An existing completed-run screen can be shown with that label instead of spending on a retake.

The model chooses `details` or `diff`; Python translates that into the official MCP `pull_request_read` call. The model cannot choose another repo/PR, request a write method, execute code, browse URLs, or read local files through the available tool. Both views must be read before a brief is shown. These controls do not prove that the generated summary is correct: inspect it against the diff.

### If a run stops

`mcp_connected` confirms the local server handshake and tool inventory, not GitHub permissions or OpenAI access. Run `scripts/run_secure.py --mode smoke` first to verify GitHub reads without a model call. Once that passes, use `--mode live` within the existing approved budget.

Failures now emit a sanitized `run_failed` event with a stage and category, plus an HTTP status and strictly validated request ID when available. Async exception groups preserve these safe diagnostics. No raw upstream body, traceback, key, prompt, or MCP stderr is printed. A 401 suggests authentication; 403 permissions; 404 model/endpoint access; 429 rate limits or quota. HTTP status alone cannot identify every underlying cause. Unknown request-ID formats are omitted rather than displayed.

For a 429, the handler reads at most 8 KiB plus one overflow-detection byte in memory and maps recognized error codes/types to fixed categories: exhausted credits, project/organization spend limits, organization usage limits, insufficient quota, or temporary rate limits. Raw messages and unknown codes are never printed or saved. Malformed or oversized responses retain the generic category. This improves the next attempt's diagnosis; it cannot recover a previously discarded error body.

Share only the sanitized event and fixed `STOPPED` message when troubleshooting. Keep the cumulative budget ledger: reservations are not actual billed charges, and a failed attempt is not automatically refunded by the local guard. Never disable TLS verification, broaden permissions blindly, or reset the ledger to get a run through.

## Rotate or recover

**Routine rotation:** create a replacement token at GitHub with the same intended scope → update the same 1Password item field → restart the tool → smoke test → revoke the old token after approved overlap. The code/reference stay unchanged. Running processes retain old values until restarted; no automatic hot reload is claimed.

**Suspected leak:** revoke the old token at GitHub promptly, accepting interruption if required → create replacement → update 1Password → restart and verify → review exposure/audit evidence. Updating the vault alone does not revoke a copied GitHub token.

**Lost local copy:** if the valid secret is still in 1Password and access remains authorized, the next startup retrieves it without redistributing plaintext. If neither the issuer nor the vault can recover it, issue a replacement. 1Password does not recover arbitrary lost, deleted, or revoked credentials.

**Switching:** the same variable/reference can carry a new token or service identity with compatible permissions. Changing providers, endpoints, scopes, or GitHub PAT → GitHub App can require configuration/code changes. Do not call those changes universally zero-code.

See [docs/rotation-runbook.md](docs/rotation-runbook.md) for the recording-safe checklist.

## Production applicability and limits

- Same non-interactive startup pattern can run in a protected workload. No container/cloud deployment has been verified in this revision.
- For long-lived organizational GitHub automation, prefer a GitHub App with scoped installation permissions and short-lived installation tokens. The pinned server exposes App authentication flags; this PAT demo does not implement or verify that separate route.
- No model shell tool is exposed. A coding agent that can execute arbitrary code needs a separate restricted tool runtime/broker plus network/access controls. An environment variable is not a sandbox.
- Repository content is untrusted. Read-only tools prevent writes via this interface, not disclosure or misinterpretation of permitted reads. Secret-pattern checks are best-effort guards, not comprehensive DLP.
- The adapter forwards only the required PR metadata and diff, validates their shape, and rejects recognizable GitHub, model-provider, and 1Password service-account token patterns. It cannot reliably detect arbitrary, split, or encoded credentials. Do not use those checks as permission to submit sensitive PRs.
- Logs contain fixed event names, tool/view, timing, counts, and sanitized failure metadata; no raw MCP stderr or prompts. Final PR briefs can still contain private code, so only synthetic content is permitted here.
- No proof of tenant isolation, full prompt-injection resistance, deployment hardening, rotation latency, or PR-speed improvement is claimed.

## Official references

- [GitHub MCP](https://github.com/github/github-mcp-server) · [server configuration](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md)
- [GitHub PAT guidance and GitHub App recommendation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [1Password service accounts](https://www.1password.dev/service-accounts/get-started) · [op run](https://www.1password.dev/cli/reference/commands/run)
- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)

Independent educational demo. Not an official 1Password or GitHub release. No customer/employer data or affiliation claims.
