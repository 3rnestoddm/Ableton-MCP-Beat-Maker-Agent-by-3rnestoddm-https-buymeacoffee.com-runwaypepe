import io
import json
import importlib.util
from pathlib import Path

import pytest


def load_module():
    """Load the target module directly from the repo path."""
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "integrations" / "ableton" / "ableton_mcp_server.py"
    assert module_path.exists(), f"Missing target file: {module_path}"

    spec = importlib.util.spec_from_file_location("ableton_mcp_server", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mcp():
    return load_module()


def test_tools_list_returns_tool_schema(mcp, monkeypatch):
    fake_tools = [
        {
            "name": "ableton_status",
            "description": "Get Ableton status",
            "inputSchema": {"type": "object"},
        }
    ]

    monkeypatch.setattr(mcp, "tool_schema", lambda: fake_tools)

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }

    response = mcp.handle_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert response["result"] == {"tools": fake_tools}


def test_tools_call_returns_tool_result(mcp, monkeypatch):
    def fake_tool_result(name):
        assert name == "ableton_status"
        return {"content": [{"type": "text", "text": "ok"}]}

    monkeypatch.setattr(mcp, "tool_result", fake_tool_result)

    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "ableton_status",
            "arguments": {},
        },
    }

    response = mcp.handle_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 2
    assert "result" in response
    assert response["result"] == {"content": [{"type": "text", "text": "ok"}]}


def test_tools_call_invalid_tool_returns_invalid_params_error(mcp, monkeypatch):
    def fake_tool_result(name):
        raise ValueError(f"Unknown tool: {name}")

    monkeypatch.setattr(mcp, "tool_result", fake_tool_result)

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "does_not_exist",
            "arguments": {},
        },
    }

    response = mcp.handle_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 3
    assert "error" in response
    assert response["error"]["code"] == -32602
    assert "does_not_exist" in response["error"]["message"]


def test_unknown_method_returns_method_not_found(mcp):
    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "not/a/real_method",
        "params": {},
    }

    response = mcp.handle_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 4
    assert "error" in response
    assert response["error"]["code"] == -32601
    assert "Method not found" in response["error"]["message"]


def test_main_skips_blank_lines_and_writes_one_response_per_request(mcp, monkeypatch):
    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/list",
        "params": {},
    }

    monkeypatch.setattr(mcp, "tool_schema", lambda: [{"name": "ableton_paths"}])

    fake_stdin = io.StringIO("\n" + json.dumps(request) + "\n\n")
    fake_stdout = io.StringIO()

    monkeypatch.setattr(mcp.sys, "stdin", fake_stdin)
    monkeypatch.setattr(mcp.sys, "stdout", fake_stdout)

    exit_code = mcp.main()

    assert exit_code == 0

    output_lines = [line for line in fake_stdout.getvalue().splitlines() if line.strip()]
    assert len(output_lines) == 1

    payload = json.loads(output_lines[0])
    assert payload["id"] == 5
    assert payload["result"] == {"tools": [{"name": "ableton_paths"}]}


def test_main_wraps_unhandled_exception_in_internal_error(mcp, monkeypatch):
    def boom(_request):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(mcp, "handle_request", boom)

    fake_stdin = io.StringIO('{"jsonrpc":"2.0","id":6,"method":"tools/list","params":{}}\n')
    fake_stdout = io.StringIO()

    monkeypatch.setattr(mcp.sys, "stdin", fake_stdin)
    monkeypatch.setattr(mcp.sys, "stdout", fake_stdout)

    exit_code = mcp.main()

    assert exit_code == 0

    output = fake_stdout.getvalue().strip()
    payload = json.loads(output)

    assert payload["jsonrpc"] == "2.0"
    assert payload["id"] is None
    assert payload["error"]["code"] == -32000
    assert "kaboom" in payload["error"]["message"]


def test_tools_call_ignores_arguments_in_current_implementation(mcp, monkeypatch):
    seen = {}

    def fake_tool_result(name):
        seen["name"] = name
        return {"ok": True}

    monkeypatch.setattr(mcp, "tool_result", fake_tool_result)

    request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "ableton_status",
            "arguments": {"foo": "bar"},
        },
    }

    response = mcp.handle_request(request)

    assert seen["name"] == "ableton_status"
    assert response["result"] == {"ok": True}
