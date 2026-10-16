---
title: MCP positioned screenshots ignore the named camera's projection and FOV
topic: unity-editor-scripting-mcp
tags: [mcp, manage_camera, screenshot, orthographic, fov, floor plan]
summary: manage_camera screenshot with view_position/view_rotation renders through a temporary ~60° perspective camera; frame top-down plans by distance instead of setting orthographic.
---
**Symptom:** Setting `orthographic`, `orthographicSize` or `fieldOfView` on the named camera has no effect on a positioned capture; plans come back perspective with walls clipped.
**Cause:** The MCP `manage_camera action=screenshot` with `view_position`/`view_rotation` uses a temporary default ~60° perspective camera.
**Fix / rule:**
- Frame by distance: visible half-height ≈ `(camY − subjectY) × 0.577` at 60° FOV; solve for camY and shoot with `view_rotation [90,0,0]`. Add margin for tall geometry (closer to the camera, projects larger): a 60 × 60 m plate with 10 m tall geometry needs about `y = 64`.
- Pass `include_image: true` and `max_resolution: 1600`; otherwise the image is 640 px wide and labels are unreadable. `screenshot_super_size` does nothing on positioned captures.
