"""Validate MCP shape, constrain methods, minimize the content sent to the model."""

import json
from agent import safe_text, tool_arguments
from demo_errors import DemoError


def validate_inventory(inventory):
    if inventory.next_cursor:
        raise DemoError("Unexpected paginated tool inventory.")
    if {tool.name for tool in inventory.tools} != {"pull_request_read"} or len(inventory.tools) != 1:
        raise DemoError("MCP tool inventory is broader than the approved one-tool contract.")


class GitHubReader:
    def __init__(self, cfg, session):
        self.cfg, self.session = cfg, session

    async def read(self, args):
        params = tool_arguments(self.cfg, args)
        try:
            result = await self.session.call_tool("pull_request_read", params, read_timeout_seconds=25)
        except Exception:
            raise DemoError("GitHub MCP tool call failed before a usable result. Run smoke mode to isolate GitHub access without calling the model.", stage="github_mcp", category="tool_transport_failure") from None
        if getattr(result, "is_error", True):
            raise DemoError("GitHub tool returned an error; no brief produced. Check the PAT's selected repository, expiry, and Pull requests read permission.", stage="github_mcp", category="tool_reported_error")
        blocks = result.content
        if not blocks or any(getattr(b, "type", None) != "text" or not isinstance(getattr(b, "text", None), str) for b in blocks):
            raise DemoError("Unexpected non-text GitHub response.", stage="github_mcp", category="invalid_tool_response")
        text = safe_text("\n".join(b.text for b in blocks))
        if args["view"] == "details":
            try:
                data = json.loads(text)
            except ValueError:
                raise DemoError("Unexpected PR metadata format.", stage="github_mcp", category="invalid_tool_response") from None
            if not isinstance(data, dict) or not isinstance(data.get("title"), str):
                raise DemoError("PR title missing from metadata.", stage="github_mcp", category="invalid_tool_response")
            if type(data.get("number")) is not int or data["number"] != self.cfg.pull_number or data.get("html_url") != self.cfg.url:
                raise DemoError("GitHub returned an unexpected PR identity.", stage="github_mcp", category="unexpected_pr_identity")
            body = data.get("body")
            if body is not None and not isinstance(body, str):
                raise DemoError("Unexpected PR description format.", stage="github_mcp", category="invalid_tool_response")
            # Forward only the fields the brief needs, not arbitrary metadata.
            return {"url": self.cfg.url, "title": safe_text(data["title"], 500), "body": safe_text(body if body is not None else "", 5000)}
        if not text.strip():
            raise DemoError("PR diff was empty.", stage="github_mcp", category="empty_diff")
        return {"url": self.cfg.url, "diff": text}
