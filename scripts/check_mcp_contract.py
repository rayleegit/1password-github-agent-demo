"""Protocol-only inspection with a deliberately invalid token; no tools called."""

import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mcp_adapter import validate_inventory


async def main():
    params = StdioServerParameters(
        command=str(ROOT / "vendor/github-mcp-server"),
        args=["stdio", "--read-only", "--tools=pull_request_read"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": "github_pat_INVALID_PROTOCOL_TEST_ONLY"},
    )
    with open(os.devnull, "w") as errlog:
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=10) as session:
                info = await session.initialize()
                inventory = await session.list_tools()
                validate_inventory(inventory)
                schema = inventory.tools[0].input_schema
                required = {"method", "owner", "repo", "pullNumber"}
                if not required.issubset(set(schema["required"])):
                    raise RuntimeError("Tool schema differs from expected contract")
                methods = schema["properties"]["method"]["enum"]
                if not {"get", "get_diff"}.issubset(methods):
                    raise RuntimeError("Read methods missing")
                print(json.dumps({"mode": "protocol-only", "server_version": info.server_info.version, "tools": [t.name for t in inventory.tools], "methods_checked": ["get", "get_diff"], "github_tool_calls": 0, "model_calls": 0, "credential_valid": False}))


if __name__ == "__main__":
    asyncio.run(main())
