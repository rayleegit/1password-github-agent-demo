# Credential rotation and recovery

This procedure applies to the disposable, scoped GitHub token used by this example. Follow your organization's authorization and incident-response procedures for production credentials. The demo does not automate issuance or revocation.

## Routine rotation

1. Confirm that the existing configuration passes `agent.py --mode smoke` with the current credential. Do not print its value.
2. Create a replacement at GitHub with the required repository scope, read permissions, and expiry.
3. Update the same credential field in the 1Password item. The `op://` reference can stay unchanged.
4. Stop the old tool process. Start a new smoke run so `op run` retrieves the current value. Running processes do not automatically reload a changed vault item.
5. Confirm that PR details and diff reads succeed. An unchanged source tree alone does not prove the replacement credential was used.
6. Revoke the old credential at GitHub after any authorized overlap, then verify the replacement still works.

## Suspected exposure

Revoke the affected credential at GitHub promptly, accepting interruption if needed. Issue a replacement, update the vault item, restart consumers, and verify access. Review relevant audit evidence. Editing or deleting the vault item does not invalidate copies of a token held elsewhere.

If the 1Password service-account token was exposed, rotate or revoke that credential separately and review its vault access. Changing the GitHub token does not repair a compromised bootstrap credential.

## Recovery and verification limits

- If a valid token remains in the vault and access is authorized, a fresh startup can retrieve it without distributing another plaintext file.
- If the credential is lost or revoked, issue a replacement. The example cannot recover arbitrary deleted credentials.
- Use approved disposable credentials for negative-access testing. A denied startup should stop before GitHub reads or model calls. A timeout is inconclusive, not proof of denial.
- The recorded successful access run does not verify rotation, revocation, denied access, or recovery. These lifecycle procedures have not been exercised end to end in the current evidence.
- No automatic hot reload, zero downtime, or rotation-latency guarantee is provided.
