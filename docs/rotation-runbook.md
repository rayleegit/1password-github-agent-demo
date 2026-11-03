# Rotation recording checklist

Do not change or revoke production credentials for a demo. Use disposable, scoped credentials for the synthetic repository; obtain approval before issuing or modifying them.

1. Confirm a real smoke test passes with credential A. Do not print its value or hashes.
2. At GitHub, create credential B with matching minimum permissions and expiry. Keep issuance off camera.
3. Update the existing 1Password item's credential field. Record only the field name/masked value and save confirmation; no clipboard, browser password reveal, or raw shell history.
4. Exit the old tool process. A new `agent.py --mode smoke` invocation starts a fresh `op run` and retrieves the current value.
5. Confirm PR reads succeed with B and the source tree/config reference are unchanged. `git diff --exit-code` is only code-change evidence, not proof that B was used.
6. Revoke A at GitHub with approval. Then a fresh smoke run succeeding is stronger evidence of B's use. Do not display token values to prove identity.
7. For a denied-start recording, use invalid 1Password authentication in a fresh, clean process with no interactive fallback. It must fail before the GitHub tool starts and before a model call. Never reuse previous PR context as a success.
8. Record measured durations only if you actually time the entire defined procedure. No fabricated percentage, universal seconds-to-rotate claim, hot reload, or zero-downtime claim.

Value you can state: one controlled place to update the stored secret; fewer manual plaintext copies; stable application reference; repeatable restart and verification. Provider issuance/revocation and each consumer restart remain separate responsibilities.

Current evidence (1 November 2026): the recorded live-run transcript shows two GitHub reads and three model responses. Live replacement/revocation and denied-start checks remain unverified. Successful access does not establish those negative/lifecycle checks. Present rotation as an instructional procedure until it is tested with approved disposable credentials.
