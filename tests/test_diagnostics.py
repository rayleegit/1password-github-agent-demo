"""Offline diagnostics tests: no credentials, network, or real budget mutations."""

import contextlib
import io
import json
import runpy
import ssl
import unittest
import urllib.error
from unittest.mock import patch

import agent


REQUEST_ID = "req_" + "a" * 32


class DiagnosticTests(unittest.TestCase):
    def report(self, exc):
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream):
            agent.report_failure(exc)
        return stream.getvalue()

    def http_error(self, status, request_id=REQUEST_ID, body=b"RAW-BODY-CANARY"):
        return urllib.error.HTTPError(
            "https://example.invalid/private-canary", status, "RAW-ERROR-CANARY",
            {"x-request-id": request_id}, io.BytesIO(body),
        )

    def test_nested_group_keeps_safe_category(self):
        failure = agent.model_http_failure(self.http_error(401))
        output = self.report(ExceptionGroup("PRIVATE-GROUP-CANARY", [ExceptionGroup("PRIVATE-NESTED", [failure])]))
        event = json.loads(output.splitlines()[0])
        self.assertEqual(event, {"event": "run_failed", "stage": "openai", "category": "authentication_failed", "http_status": 401, "request_id": REQUEST_ID})
        self.assertNotIn("CANARY", output)

    def test_unknown_error_never_prints_its_message(self):
        output = self.report(ExceptionGroup("PRIVATE-GROUP", [RuntimeError("SECRET-CANARY")]))
        self.assertIn("dependency_or_transport_failure", output)
        self.assertNotIn("SECRET-CANARY", output)
        self.assertNotIn("PRIVATE-GROUP", output)

    def test_arbitrary_request_id_is_not_printed(self):
        for value in ("SECRET-CANARY", "req_sk-" + "A" * 40, "req_" + "a" * 32 + "\nSECRET-CANARY"):
            with self.subTest(header=value):
                output = self.report(agent.model_http_failure(self.http_error(403, value)))
                self.assertNotIn("request_id", json.loads(output.splitlines()[0]))
                self.assertNotIn("CANARY", output)

    def test_http_categories(self):
        cases = {400: "request_invalid", 401: "authentication_failed", 403: "permission_denied", 404: "model_or_endpoint_unavailable", 408: "request_timeout", 429: "rate_limit_or_quota", 503: "service_error", 302: "redirect_blocked"}
        for status, category in cases.items():
            with self.subTest(status=status):
                exc = self.http_error(status)
                failure = agent.model_http_failure(exc)
                self.assertEqual(failure.category, category)
                if status != 429:
                    self.assertEqual(exc.fp.tell(), 0)  # Only 429 needs bounded code inspection.

    def test_429_codes_are_classified_without_message_disclosure(self):
        cases = {
            "credit_balance_exhausted": "credits_exhausted",
            "organization_spend_limit_exceeded": "organization_spend_limit",
            "project_spend_limit_exceeded": "project_spend_limit",
            "organization_usage_limit_exceeded": "organization_usage_limit",
            "insufficient_quota": "insufficient_quota",
            "rate_limit_exceeded": "temporary_rate_limit",
            "slow_down": "temporary_rate_limit",
        }
        for code, category in cases.items():
            with self.subTest(code=code):
                exc = self.http_error(429, body=json.dumps({"error": {"code": code, "message": "PRIVATE-KEY-CANARY", "param": "PRIVATE-PROMPT-CANARY"}}).encode())
                failure = agent.model_http_failure(exc)
                self.assertEqual(failure.category, category)
                self.assertNotIn("CANARY", self.report(failure))

    def test_429_bad_or_large_bodies_keep_generic_category(self):
        bodies = [b"not json", b"x" * 9000, b"[]", b'{"error":[]}', b'{"error":{"code":["private"]}}', b'{"error":{"code":"PRIVATE-CODE-CANARY"}}']
        for body in bodies:
            with self.subTest(length=len(body)):
                exc = self.http_error(429, body=body)
                failure = agent.model_http_failure(exc)
                self.assertEqual(failure.category, "rate_limit_or_quota")
                self.assertLessEqual(exc.fp.tell(), 8193)
                self.assertNotIn("CANARY", self.report(failure))

    def test_429_type_fallback_and_specific_code_precedence(self):
        cases = [
            ({"type": "insufficient_quota", "code": None}, "insufficient_quota"),
            ({"type": "rate_limit_error", "code": None}, "temporary_rate_limit"),
            ({"type": "insufficient_quota", "code": "credit_balance_exhausted"}, "credits_exhausted"),
        ]
        for error, category in cases:
            with self.subTest(category=category):
                exc = self.http_error(429, body=json.dumps({"error": error}).encode())
                self.assertEqual(agent.model_http_failure(exc).category, category)

    def test_provider_http_error_does_not_expose_key_or_body(self):
        with patch("budget.reserve_request"), patch("urllib.request.build_opener") as opener, contextlib.redirect_stdout(io.StringIO()):
            opener.return_value.open.side_effect = self.http_error(429)
            with self.assertRaises(agent.DemoError) as raised:
                agent.OpenAIResponses("KEY-CANARY").create({})
        output = self.report(raised.exception)
        self.assertIn("rate_limit_or_quota", output)
        self.assertNotIn("CANARY", output)

    def test_provider_credential_is_in_auth_header_not_request_body_or_events(self):
        payload = {"input": [{"role": "user", "content": "SYNTHETIC-PR-CANARY"}]}
        events = io.StringIO()
        with patch("budget.reserve_request"), patch("urllib.request.build_opener") as opener, contextlib.redirect_stdout(events):
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = b'{"status":"completed","output":[]}'
            agent.OpenAIResponses("PROVIDER-KEY-CANARY").create(payload)
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer PROVIDER-KEY-CANARY")
        self.assertEqual(json.loads(request.data), payload)
        self.assertNotIn("PROVIDER-KEY-CANARY", request.data.decode())
        self.assertNotIn("CANARY", events.getvalue())

    def test_connection_errors_are_safely_classified(self):
        cases = [
            (urllib.error.URLError(ssl.SSLCertVerificationError(1, "PRIVATE-CERT")), "tls_verification_failed"),
            (urllib.error.URLError(TimeoutError("PRIVATE-TIMEOUT")), "connection_timeout"),
            (urllib.error.URLError("PRIVATE-HOST"), "connection_failed"),
            (TimeoutError("PRIVATE-TIMEOUT"), "request_timeout"),
        ]
        for error, category in cases:
            with self.subTest(category=category), patch("budget.reserve_request"), patch("urllib.request.build_opener") as opener, contextlib.redirect_stdout(io.StringIO()):
                opener.return_value.open.side_effect = error
                with self.assertRaises(agent.DemoError) as raised:
                    agent.OpenAIResponses("KEY-CANARY").create({})
                self.assertEqual(raised.exception.category, category)
                self.assertNotIn("PRIVATE", self.report(raised.exception))

    def test_budget_rejection_precedes_network(self):
        with patch("budget.reserve_request", side_effect=agent.DemoError("Local budget exhausted.")), patch("urllib.request.build_opener") as opener:
            with self.assertRaises(agent.DemoError) as raised:
                agent.OpenAIResponses("KEY-CANARY").create({})
            self.assertEqual(raised.exception.stage, "model_preflight")
            self.assertEqual(raised.exception.category, "budget_guard")
            opener.assert_not_called()

    def test_main_unwraps_task_group(self):
        import asyncio
        async def failing_run(*args, **kwargs):
            async with asyncio.TaskGroup():
                raise agent.model_http_failure(self.http_error(401))
        output = io.StringIO()
        with patch("sys.argv", ["agent.py", "--mode", "live", "--approve-model-call"]), patch("agent.live_run", new=failing_run), contextlib.redirect_stderr(output):
            code = agent.main()
        self.assertEqual(code, 1)
        self.assertIn('"category": "authentication_failed"', output.getvalue())
        self.assertNotIn("CANARY", output.getvalue())

    def test_script_entrypoint_shares_budget_error_type(self):
        import budget
        namespace = runpy.run_path(str(agent.ROOT / "agent.py"), run_name="diagnostic_entrypoint")
        self.assertIs(namespace["DemoError"], budget.DemoError)

    def test_github_transport_error_is_sanitized(self):
        import asyncio
        from mcp_adapter import GitHubReader
        class Session:
            async def call_tool(self, *args, **kwargs):
                raise RuntimeError("PRIVATE-TOKEN-CANARY")
        cfg = agent.Config.load(agent.ROOT / "demo.example.json")
        with self.assertRaises(agent.DemoError) as raised:
            asyncio.run(GitHubReader(cfg, Session()).read({"view": "details"}))
        self.assertEqual(raised.exception.stage, "github_mcp")
        self.assertNotIn("CANARY", self.report(raised.exception))


if __name__ == "__main__":
    unittest.main()
