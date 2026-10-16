---
title: Free CC0 asset sources with scriptable downloads, and what to avoid
topic: assets-sourcing
tags: [cc0, poly haven, ambientcg, quaternius, itch.io, sketchfab, built-in rp, piracy]
summary: Poly Haven, ambientCG and Quaternius are CC0 and downloadable by script; avoid 'free download' mirrors of paid packs and URP/HDRP-only packs for VRChat.
sources: [https://polyhaven.com/, https://ambientcg.com/, https://quaternius.com/, https://sketchfab.com/, https://vpm.techanon.dev/index.json]
---
**Sources:**
- **Poly Haven** (CC0): list `https://api.polyhaven.com/assets?t=models`, files via `https://api.polyhaven.com/files/<id>`. 2K FBX + textures; `*_nor_gl_*.exr` is an OpenGL normal (set importer to Normal Map). Set FBX `materialImportMode=None`, enable `generateSecondaryUV`. Blender-exported FBX may import lying on its side — apply `Euler(-90,0,0)` then yaw. Merged meshes can be split headless with Blender `bpy.ops.mesh.separate(type='LOOSE')`.
- **ambientCG** (CC0 materials): `https://ambientcg.com/get?file=<AssetID>_2K-JPG.zip`; search `https://ambientcg.com/api/v2/full_json?q=…&type=Material`.
- **Quaternius** (CC0 megakits: medieval village modular pieces — you assemble buildings yourself, fantasy props, nature, dungeon, weapons). Models use `MI_*` materials over trim-sheet PNGs. Free tier on itch.io downloads without an account: GET pack page → scrape `csrf_token` → `POST {slug}/download_url` → GET returned URL → scrape `data-upload_id` (only the $0 tier has one; `data-screenshot_id` is not it) → `POST {slug}/file/<upload_id>?source=game_download` with csrf → signed CDN URL that expires in ~60 s. Keep one `requests.Session` for cookies.
- **Sketchfab** via the Unity MCP `import_model` (search/preview/import, API key in the editor). Check `isDownloadable` — many "free" models are not. Imports land as glTF via glTFast.
- **ProTV** installs from VPM repo `https://vpm.techanon.dev/index.json` (needs dev.architech.sdk too). After extracting into `Packages/`, call `UnityEditor.PackageManager.Client.Resolve()`.
**Avoid:**
- "Free download" sites like `unityassetcollection.com` / `unityunreal.com` are piracy mirrors of paid Asset Store packs. Always confirm price on assetstore.unity.com.
- VRChat worlds are Built-in RP; URP/HDRP-only packs import magenta — meshes/textures survive, every material needs rebuilding.
**Tip:** Keep a downloads index file in the project root listing what was sourced and from where.
