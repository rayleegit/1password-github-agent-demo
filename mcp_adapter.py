"""Validate MCP shape, constrain methods, minimize the content sent to the model."""

import json
from agent import DemoError, safe_text, tool_arguments


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
        result = await self.session.call_tool("pull_request_read", params, read_timeout_seconds=25)
        if getattr(result, "is_error", True):
            raise DemoError("GitHub tool returned an error; no brief produced.")
        blocks = result.content
        if not blocks or any(getattr(b, "type", None) != "text" for b in blocks):
            raise DemoError("Unexpected non-text GitHub response.")
        text = safe_text("\n".join(b.text for b in blocks))
        if args["view"] == "details":
            try:
                data = json.loads(text)
            except ValueError:
                raise DemoError("Unexpected PR metadata format.") from None
            if not isinstance(data, dict) or not isinstance(data.get("title"), str):
                raise DemoError("PR title missing from metadata.")
            if data.get("number") != self.cfg.pull_number or data.get("html_url") != self.cfg.url:
                raise DemoError("GitHub returned an unexpected PR identity.")
            return {"url": self.cfg.url, "title": safe_text(data["title"], 500), "body": safe_text(data.get("body") or "", 5000), "state": data.get("state")}
        if not text.strip():
            raise DemoError("PR diff was empty.")
        return {"url": self.cfg.url, "diff": text}
