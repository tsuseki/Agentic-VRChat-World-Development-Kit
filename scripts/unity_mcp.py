#!/usr/bin/env python3
"""Minimal stdio MCP client for the MCP for Unity (CoplayDev unity-mcp) server.

Lets an agent (or you, from a shell) call a single Unity MCP tool without an
MCP-capable host.

Requirements:
  - uv installed, with `uvx` on PATH (https://docs.astral.sh/uv/).
  - The "MCP for Unity" package installed in the Unity project
    (see install-unity-mcp.py).
  - The server package already in the uv cache: SERVER_CMD uses --offline, so
    run `uvx --from mcpforunityserver==10.0.0 mcp-for-unity --transport stdio`
    once while online, or remove "--offline" from SERVER_CMD. The server
    version is pinned to the same tag as PACKAGE_URL in install-unity-mcp.py;
    bump both together.
  - The Unity project open in the Editor with the MCP bridge running.

Usage:
  python unity_mcp.py --list
  python unity_mcp.py --schema <tool_name>
  python unity_mcp.py <tool_name> [json_args]
  python unity_mcp.py <tool_name> --args-file <path.json>

Spawns the same server an MCP client would (uvx --from mcpforunityserver
mcp-for-unity), does the MCP
handshake, calls one tool, prints the result text, exits. Exit code is 1 when
the tool reports an error.
"""
import json
import shutil
import subprocess
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SERVER_CMD = [
    shutil.which("uvx") or "uvx",
    "--offline",
    "--from", "mcpforunityserver==10.0.0",  # same tag as install-unity-mcp.py PACKAGE_URL
    "mcp-for-unity", "--transport", "stdio",
]

TIMEOUT = 180  # some Unity ops (imports, bakes) are slow


class McpClient:
    def __init__(self):
        self.proc = subprocess.Popen(
            SERVER_CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
        self.next_id = 1
        self.responses = {}
        self.lock = threading.Condition()
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()

    def _read_loop(self):
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in msg and ("result" in msg or "error" in msg):
                with self.lock:
                    self.responses[msg["id"]] = msg
                    self.lock.notify_all()

    def _send(self, obj):
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params=None, timeout=TIMEOUT):
        rid = self.next_id
        self.next_id += 1
        req = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            req["params"] = params
        self._send(req)
        deadline = time.time() + timeout
        with self.lock:
            while rid not in self.responses:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError(f"no response to {method} within {timeout}s")
                self.lock.wait(remaining)
            return self.responses.pop(rid)

    def notify(self, method, params=None):
        obj = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            obj["params"] = params
        self._send(obj)

    def handshake(self):
        r = self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "unity-mcp-cli", "version": "1.0"},
        }, timeout=60)
        if "error" in r:
            raise RuntimeError(f"initialize failed: {r['error']}")
        self.notify("notifications/initialized")

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2

    client = McpClient()
    try:
        client.handshake()
        if args[0] == "--list":
            r = client.request("tools/list", {})
            tools = r.get("result", {}).get("tools", [])
            for t in tools:
                desc = (t.get("description") or "").split("\n")[0][:110]
                print(f"{t['name']}: {desc}")
            return 0

        if args[0] == "--schema":
            r = client.request("tools/list", {})
            tools = r.get("result", {}).get("tools", [])
            for t in tools:
                if t["name"] == args[1]:
                    print(json.dumps(t, indent=2))
                    return 0
            print(f"tool {args[1]} not found")
            return 1

        tool = args[0]
        tool_args = {}
        if len(args) >= 3 and args[1] == "--args-file":
            with open(args[2], encoding="utf-8-sig") as f:
                tool_args = json.load(f)
        elif len(args) >= 2:
            tool_args = json.loads(args[1])

        r = client.request("tools/call", {"name": tool, "arguments": tool_args})
        if "error" in r:
            print(json.dumps(r["error"], indent=2))
            return 1
        result = r["result"]
        for item in result.get("content", []):
            if item.get("type") == "text":
                print(item["text"])
            else:
                print(json.dumps(item))
        return 1 if result.get("isError") else 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
