# Security boundaries

This is a teaching demo with synthetic data, not a complete secure-agent platform.

Trust boundaries: model → fixed application function → official MCP process → GitHub API. The parent is trusted and holds bootstrap/provider credentials. `op run` resolves the GitHub credential in a child. The final MCP child drops the bootstrap and provider credentials. Same-host isolation is NOT supplied by this process/environment separation.

The application rejects a broadened MCP inventory, any model-requested repo override, write method, unknown tool, duplicate view, oversized response, and incomplete read sequence. It suppresses raw upstream errors. Model assertions are not used to enforce permissions.

Only two MCP methods are callable through the harness: `get` and `get_diff`. Operator-controlled configuration fixes owner/repo/PR. GitHub token scopes are a separate layer. There are no application write endpoints or arbitrary command tools.

The details adapter validates the PR identity and forwards only its canonical URL, title, and description; the diff path returns the canonical URL and diff. A bounded pattern check rejects recognizable GitHub, model-provider, and 1Password service-account token strings before forwarding tool data or displaying a final brief. These are best-effort checks, not a complete secret scanner or prompt-injection defense. Unknown formats and encoded or split secrets can evade them.

Diagnostic events contain metadata, not PR text. The final brief contains PR information, and a saved terminal transcript can contain that brief. Do not describe the entire terminal output as sanitized telemetry. The model-provider credential goes in its API authorization header, not the model's messages; the provider necessarily receives it for authentication.

The public synthetic repository is convenient for reproduction, but a successful read cannot establish private-repository authorization or read-only token scopes. Verify actual GitHub and 1Password permissions separately. A vault item named "GitHub Read Token" does not enforce either policy.

Do not upload real sensitive code to a model without approval. `store:false` is not equivalent to contractual zero retention. No repository code is executed. Untrusted PR text can still influence a model's answer; verify its claims.

Rotate leaked credentials at the issuing service. Editing/removing a 1Password item does not invalidate a token already held elsewhere. Protect the 1Password service-account token and replace it separately if compromised.

Report issues without including credentials, customer data, or private PR content. Do not place real secrets in repository issues or pull requests.
