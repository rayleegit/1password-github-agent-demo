# Security boundaries

This is a teaching demo with synthetic data, not a complete secure-agent platform.

Trust boundaries: model → fixed application function → official MCP process → GitHub API. The parent is trusted and holds bootstrap/provider credentials. `op run` resolves the GitHub credential in a child. The final MCP child drops the bootstrap and provider credentials. Same-host isolation is NOT supplied by this process/environment separation.

The application rejects a broadened MCP inventory, any model-requested repo override, write method, unknown tool, duplicate view, oversized response, and incomplete read sequence. It suppresses raw upstream errors. Model assertions are not used to enforce permissions.

Only two MCP methods are callable through the harness: `get` and `get_diff`. Operator-controlled configuration fixes owner/repo/PR. GitHub token scopes are a separate layer. There are no application write endpoints or arbitrary command tools.

Do not upload real sensitive code to a model without approval. `store:false` is not equivalent to contractual zero retention. No repository code is executed. Untrusted PR text can still influence a model's answer; verify its claims.

Rotate leaked credentials at the issuing service. Editing/removing a 1Password item does not invalidate a token already held elsewhere. Protect the 1Password service-account token and replace it separately if compromised.

Report issues without including credentials, customer data, or private PR content. Do not place real secrets in repository issues or pull requests.
