"""Add the MCP for Unity (CoplayDev unity-mcp) package to a Unity project's
Packages/manifest.json, backing the original up as manifest.json.before-mcp.

Usage: python install-unity-mcp.py PROJECT_ROOT

For closed Unity projects only; wait for any project/package manager operations first.
Check for embedded/Assets MCP installations before running. For an open project,
use Unity Package Manager > Add package from git URL with PACKAGE_URL below.
After installation, wait for compilation, check the console, and verify the
project in mcpforunity://instances. A manifest entry alone is not connectivity.
Keep manifest.json.before-mcp until successful resolution, then remove it.
"""
PACKAGE_URL = "https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.0.0"

import json
import sys
from pathlib import Path

project = Path(sys.argv[1]).resolve()
if not (project / "ProjectSettings/ProjectVersion.txt").is_file():
    raise SystemExit("Not a Unity project")
if (project / "Temp/UnityLockfile").exists():
    raise SystemExit("Unity lock exists; use the editor or establish that it is closed")
manifest = project / "Packages/manifest.json"
original = manifest.read_bytes()
data = json.loads(original.decode("utf-8-sig"))
dependencies = data["dependencies"]
name = "com.coplaydev.unity-mcp"
if name in dependencies:
    print("MCP dependency already present; unchanged")
else:
    dependencies[name] = PACKAGE_URL
    backup = manifest.with_name("manifest.json.before-mcp")
    with backup.open("xb") as stream:
        stream.write(original)
    if manifest.read_bytes() != original:
        raise SystemExit("Manifest changed during setup; stopped without overwriting")
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("MCP dependency added; open Unity to resolve and compile it")
