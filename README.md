# PR brief, without a key in the prompt

A bounded Python agent reads **one configured pull request** using GitHub's official MCP server. 1Password CLI resolves a secret reference at startup. The model receives PR text, not the GitHub credential as part of its messages.

**Status:** implementation and offline tests are available. A live 1Password → GitHub → model run is not yet verified. Offline mode is a scripted protocol fixture, NOT an AI model or an authenticated demonstration.

## What this teaches

1. Give the agent one useful, read-only job: a three-bullet PR brief and two human-review questions.
2. Let a trusted tool process handle authentication. Keep the credential out of code and model messages.
3. Rotate a stored credential without changing the tool's application code or secret reference; start a fresh tool process to load the new value.
4. Keep the boundaries explicit: secret delivery is not a sandbox, GitHub authorization, or prompt-injection immunity.

```text
Scoped 1Password service account → op run → credential scrubber → GitHub MCP → GitHub
                                            ↑ tool calls / PR data ↓
                                      bounded Python agent → OpenAI Responses
```

The bootstrap service-account token is a secret too. It belongs in your deployment platform's protected secret configuration. The GitHub process receives only its fine-grained PAT, not the bootstrap or model-provider token. The trusted Python parent still has the bootstrap/provider tokens; this is process hygiene, NOT isolation from a hostile process on the same host.

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

- Create a short-lived fine-grained GitHub PAT for the selected **private synthetic demo repository**. Grant Pull requests: Read-only and the required automatic Metadata permission. Do not use a broad classic PAT. Verify the exact scopes against the PR endpoint. The application also hard-binds owner/repo/PR: a fine-grained PAT can still read public resources outside its selected private repositories.
- Store the PAT in a dedicated 1Password vault/item. Update `secret_ref` in `demo.local.json` with its `op://vault/item/field` reference. Prefer item/field IDs for rename resilience. No token belongs in the JSON.
- Create a service account with read access only to that dedicated vault. Supply `OP_SERVICE_ACCOUNT_TOKEN` through a protected runtime secret or an ephemeral, non-echoing local prompt. Do not commit it, put it in shell history, paste it into chat, or show it on screen.
- Set `OPENAI_API_KEY` separately for the model call. Use a supported Responses tool-calling model in `model`. The example name is not proof of access or availability on your account.
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

The approval flag is an explicit operator check, not a billing cap. Maximum four model requests, three tool calls, 900 output tokens per request, and bounded tool content. A budget cap must also be set with your provider. Live requests send the approved synthetic PR and instructions only. No implicit retries. On a tool failure, the run ends without a fabricated brief.

The model chooses `details` or `diff`; Python translates that into the official MCP `pull_request_read` call. The model cannot choose another repo/PR, request a write method, execute code, browse URLs, or read local files through the available tool. Both views must be read before a brief is shown. These controls do not prove that the generated summary is correct: inspect it against the diff.

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
- Logs contain fixed event names, tool/view, timing, and counts; no raw MCP stderr or prompts. Final PR briefs can still contain private code, so only synthetic content is permitted here.
- No proof of tenant isolation, full prompt-injection resistance, deployment hardening, rotation latency, or PR-speed improvement is claimed.

## Why GitHub, not Linear?

GitHub directly supports the PR-review use case and this account already has repository setup access. Linear also offers an official remote MCP server, including a read-only endpoint and API-key/bearer authentication, but it requires a separate workspace credential and issue fixture. It is a valid future substitution, not a shortcut around GitHub authorization.

## Official references

- [GitHub MCP](https://github.com/github/github-mcp-server) · [server configuration](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md)
- [GitHub PAT guidance and GitHub App recommendation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [1Password service accounts](https://www.1password.dev/service-accounts/get-started) · [op run](https://www.1password.dev/cli/reference/commands/run)
- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Linear MCP](https://linear.app/docs/mcp)

Independent educational demo. Not an official 1Password or GitHub release. No customer/employer data or affiliation claims.
