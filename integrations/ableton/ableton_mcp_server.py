#!/usr/bin/env python3
"""Minimal MCP-style bridge for the local Ableton install.

This is intentionally narrow. It exposes installation status and path
information so the workflow project has a stable MCP surface to extend later.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "ableton_config.json"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def tool_schema() -> list[dict[str, Any]]:
    return [
        {
            "name": "ableton_paths",
            "description": "Return detected Ableton, user library, and bridge paths.",
            "inputSchema": {"type": "object", "additionalProperties": False},
        },
        {
            "name": "ableton_status",
            "description": "Report whether the Ableton executable and related folders exist.",
            "inputSchema": {"type": "object", "additionalProperties": False},
        },
        {
            "name": "ableton_launch_instructions",
            "description": "Return the Windows command needed to launch Ableton Live.",
            "inputSchema": {"type": "object", "additionalProperties": False},
        },
    ]


def build_paths_payload() -> dict[str, Any]:
    cfg = load_config()["ableton"]
    return {
      "windows_executable": cfg["windows_executable"],
      "wsl_executable": cfg["wsl_executable"],
      "user_library_wsl": cfg["user_library_wsl"],
      "remote_scripts_wsl": cfg["remote_scripts_wsl"],
      "osc_host": cfg["osc_host"],
      "osc_port": cfg["osc_port"],
      "notes": cfg["notes"],
    }


def build_status_payload() -> dict[str, Any]:
    payload = build_paths_payload()
    return {
        "ableton_executable_exists": os.path.exists(payload["wsl_executable"]),
        "user_library_exists": os.path.exists(payload["user_library_wsl"]),
        "remote_scripts_exists": os.path.exists(payload["remote_scripts_wsl"]),
        "osc_bridge_configured": False,
        "paths": payload,
    }


def build_launch_payload() -> dict[str, Any]:
    payload = build_paths_payload()
    windows_exe = payload["windows_executable"]
    return {
        "windows_command": f'cmd.exe /C start "" "{windows_exe}"',
        "wsl_note": (
            "Launching the GUI from WSL requires invoking cmd.exe or PowerShell "
            "on the Windows side."
        ),
    }


def tool_result(name: str) -> dict[str, Any]:
    if name == "ableton_paths":
        data = build_paths_payload()
    elif name == "ableton_status":
        data = build_status_payload()
    elif name == "ableton_launch_instructions":
        data = build_launch_payload()
    else:
        raise ValueError(f"Unknown tool: {name}")
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(data, indent=2),
            }
        ]
    }


def make_response(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def make_error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": code, "message": message},
    }


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    method = request.get("method")
    msg_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return make_response(
            msg_id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "ableton-mcp-bridge", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            },
        )

    if method == "tools/list":
        return make_response(msg_id, {"tools": tool_schema()})

    if method == "tools/call":
        name = params.get("name")
        try:
            return make_response(msg_id, tool_result(name))
        except ValueError as exc:
            return make_error(msg_id, -32602, str(exc))

    return make_error(msg_id, -32601, f"Method not found: {method}")


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
        except Exception as exc:  # pragma: no cover
            response = make_error(None, -32000, str(exc))
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
