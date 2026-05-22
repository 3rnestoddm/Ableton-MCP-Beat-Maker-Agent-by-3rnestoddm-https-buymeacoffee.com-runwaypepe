# Ableton MCP Bridge

This folder connects the workflow project to the detected Ableton Live 12 Suite install.

Detected installation:

- Windows executable:
  `C:\ProgramData\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe`
- WSL path:
  `/mnt/c/ProgramData/Ableton/Live 12 Suite/Program/Ableton Live 12 Suite.exe`

## What this bridge does now

- exposes the Ableton install path through a minimal MCP-compatible stdio server
- reports whether the executable and user library are visible
- returns launch instructions for Windows or WSL-driven workflows

## What it does not do yet

- control Ableton Live sets
- inspect tracks, devices, clips, or scenes
- talk to UAD Console
- read meters from the DAW directly

## Next real integration step

For actual DAW control, add one of these layers:

1. an Ableton remote script or control surface bridge
2. an OSC bridge such as AbletonOSC
3. a Max for Live device that exposes transport, track, and device state

Once one of those is installed, the MCP bridge can be extended to expose real tools like:

- `get_set_overview`
- `list_tracks`
- `get_selected_track_devices`
- `fire_scene`
- `capture_meter_snapshot`
- `export_session_metadata`

## Local MCP server

The server entrypoint is:

- `integrations/ableton/ableton_mcp_server.py`

The config file is:

- `integrations/ableton/ableton_config.json`

## Quick run

```bash
python3 /home/c_r/workflow/integrations/ableton/ableton_mcp_server.py
```

It speaks JSON-RPC over stdio and supports:

- `initialize`
- `tools/list`
- `tools/call`
