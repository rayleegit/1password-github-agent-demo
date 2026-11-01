import asyncio
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agent import (Config, DemoError, FixtureModel, FixtureReader, ROOT, SYSTEM,
                   TOOL, clean_op_env, live_run, run_agent, safe_text, tool_arguments)
from mcp_adapter import GitHubReader, validate_inventory
from tool_process import github_env


def cfg():
    return Config.load(ROOT / "demo.example.json")


class PolicyTests(unittest.TestCase):
    def test_config_parses(self):
        self.assertEqual(cfg().owner, "rayleegit")

    def test_extra_config_key_rejected(self):
        data = json.loads((ROOT / "demo.example.json").read_text())
        data["raw_token"] = "not-allowed"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config.json"
            p.write_text(json.dumps(data))
            with self.assertRaises(DemoError):
                Config.load(p)

    def test_fixed_target_and_read_method(self):
        self.assertEqual(tool_arguments(cfg(), {"view": "diff"}), {
            "method": "get_diff", "owner": "rayleegit", "repo": "1password-github-agent-demo", "pullNumber": 1})

    def test_repository_override_rejected(self):
        with self.assertRaises(DemoError):
            tool_arguments(cfg(), {"view": "diff", "owner": "other"})

    def test_write_method_rejected(self):
        with self.assertRaises(DemoError):
            tool_arguments(cfg(), {"view": "merge"})

    def test_tool_schema_has_no_repository_or_secret_argument(self):
        self.assertEqual(set(TOOL["parameters"]["properties"]), {"view"})
        self.assertFalse(TOOL["parameters"]["additionalProperties"])

    def test_op_process_never_inherits_openai_or_raw_github_token(self):
        env = clean_op_env(cfg(), {"OP_SERVICE_ACCOUNT_TOKEN": "bootstrap-canary", "OPENAI_API_KEY": "provider-canary", "GITHUB_PERSONAL_ACCESS_TOKEN": "github-canary"})
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertEqual(env["GITHUB_PERSONAL_ACCESS_TOKEN"], cfg().secret_ref)
        self.assertEqual(env["OP_BIOMETRIC_UNLOCK_ENABLED"], "false")

    def test_bootstrap_required_no_interactive_fallback(self):
        with self.assertRaises(DemoError):
            clean_op_env(cfg(), {})

    def test_github_child_only_receives_its_credential(self):
        pat = "github_pat_" + "A" * 30
        env = github_env({"GITHUB_PERSONAL_ACCESS_TOKEN": pat, "OPENAI_API_KEY": "model-canary", "OP_SERVICE_ACCOUNT_TOKEN": "bootstrap-canary", "GITHUB_TOOLSETS": "all", "HTTPS_PROXY": "unapproved"})
        self.assertEqual(env, {"GITHUB_PERSONAL_ACCESS_TOKEN": pat})

    def test_unresolved_reference_and_classic_pat_rejected(self):
        for token in (cfg().secret_ref, "ghp_" + "A" * 30, ""):
            with self.subTest(token_type=token[:4]), self.assertRaises(ValueError):
                github_env({"GITHUB_PERSONAL_ACCESS_TOKEN": token})

    def test_output_credentials_rejected(self):
        with self.assertRaises(DemoError):
            safe_text("leaked github_pat_" + "Z" * 30)

    def test_output_cap(self):
        with self.assertRaises(DemoError):
            safe_text("x" * 18001)

    def test_control_characters_removed(self):
        self.assertEqual(safe_text("hello\x1b\x00\nworld"), "hello\nworld")

    def test_inventory_exact_one_tool(self):
        validate_inventory(SimpleNamespace(next_cursor=None, tools=[SimpleNamespace(name="pull_request_read")]))

    def test_broader_inventory_rejected(self):
        with self.assertRaises(DemoError):
            validate_inventory(SimpleNamespace(next_cursor=None, tools=[SimpleNamespace(name="pull_request_read"), SimpleNamespace(name="merge_pull_request")]))

    def test_paginated_inventory_rejected(self):
        with self.assertRaises(DemoError):
            validate_inventory(SimpleNamespace(next_cursor="more", tools=[]))


class LoopTests(unittest.IsolatedAsyncioTestCase):
    async def test_offline_fixture_is_explicit(self):
        with contextlib.redirect_stdout(io.StringIO()):
            answer = await run_agent(cfg(), FixtureReader(cfg()), FixtureModel(cfg()), "offline")
        self.assertIn("NOT AI OR LIVE GITHUB", answer)

    async def test_no_tools_no_ungrounded_answer(self):
        model = SimpleNamespace(create=lambda _: {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "I approved it."}]}]})
        with self.assertRaises(DemoError):
            await run_agent(cfg(), FixtureReader(cfg()), model, "test")

    async def test_shell_call_is_rejected(self):
        model = SimpleNamespace(create=lambda _: {"status": "completed", "output": [{"type": "function_call", "name": "exec", "call_id": "bad", "arguments": "{}"}]})
        with self.assertRaises(DemoError):
            await run_agent(cfg(), FixtureReader(cfg()), model, "test")

    async def test_multiple_calls_rejected(self):
        call = {"type": "function_call", "name": "read_pull_request", "call_id": "a", "arguments": '{"view":"diff"}'}
        model = SimpleNamespace(create=lambda _: {"status": "completed", "output": [call, call]})
        with self.assertRaises(DemoError):
            await run_agent(cfg(), FixtureReader(cfg()), model, "test")

    async def test_repeated_view_stops(self):
        model = SimpleNamespace(create=lambda _: {"status": "completed", "output": [{"type": "function_call", "name": "read_pull_request", "call_id": "a", "arguments": '{"view":"diff"}'}]})
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(DemoError):
            await run_agent(cfg(), FixtureReader(cfg()), model, "test")

    async def test_incomplete_model_response_stops(self):
        model = SimpleNamespace(create=lambda _: {"status": "incomplete", "output": []})
        with self.assertRaises(DemoError):
            await run_agent(cfg(), FixtureReader(cfg()), model, "test")

    async def test_payloads_never_include_environment_credentials(self):
        fixture = FixtureModel(cfg())
        requests = []
        def record(payload):
            requests.append(json.loads(json.dumps(payload)))
            return fixture.create(payload)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "model-canary", "OP_SERVICE_ACCOUNT_TOKEN": "bootstrap-canary", "GITHUB_PERSONAL_ACCESS_TOKEN": "tool-canary"}), contextlib.redirect_stdout(io.StringIO()):
            await run_agent(cfg(), FixtureReader(cfg()), SimpleNamespace(create=record), "test")
        serialized = json.dumps(requests)
        for value in ("model-canary", "bootstrap-canary", "tool-canary"):
            self.assertNotIn(value, serialized)
        self.assertTrue(all(p["store"] is False for p in requests))
        self.assertTrue(all(p["tools"] == [TOOL] for p in requests))

    async def test_read_error_stops_before_final_model_answer(self):
        fixture = FixtureModel(cfg())
        class BrokenReader:
            async def read(self, args):
                raise DemoError("GitHub read failed")
        with self.assertRaises(DemoError):
            await run_agent(cfg(), BrokenReader(), fixture, "test")
        self.assertEqual(fixture.turn, 1)


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_metadata_minimization(self):
        class Session:
            async def call_tool(self, name, args, **kwargs):
                return SimpleNamespace(is_error=False, content=[SimpleNamespace(type="text", text=json.dumps({"number": 1, "html_url": cfg().url, "title": "Demo", "body": "safe", "state": "open", "user": {"private_detail": "not-needed"}}))])
        data = await GitHubReader(cfg(), Session()).read({"view": "details"})
        self.assertNotIn("user", data)

    async def test_wrong_pr_rejected(self):
        class Session:
            async def call_tool(self, *args, **kwargs):
                return SimpleNamespace(is_error=False, content=[SimpleNamespace(type="text", text='{"title":"Wrong","number":99,"html_url":"https://example.invalid"}')])
        with self.assertRaises(DemoError):
            await GitHubReader(cfg(), Session()).read({"view": "details"})

    async def test_raw_error_not_forwarded(self):
        class Session:
            async def call_tool(self, *args, **kwargs):
                return SimpleNamespace(is_error=True, content=[SimpleNamespace(type="text", text="SENSITIVE ERROR")])
        with self.assertRaisesRegex(DemoError, "GitHub tool returned an error"):
            await GitHubReader(cfg(), Session()).read({"view": "diff"})

    async def test_non_text_result_rejected(self):
        class Session:
            async def call_tool(self, *args, **kwargs):
                return SimpleNamespace(is_error=False, content=[SimpleNamespace(type="image")])
        with self.assertRaises(DemoError):
            await GitHubReader(cfg(), Session()).read({"view": "diff"})


if __name__ == "__main__":
    unittest.main()
