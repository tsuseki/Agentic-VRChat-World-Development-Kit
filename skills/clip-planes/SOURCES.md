# Sources: clip-planes

Bibliography and attribution for `.omp/skills/clip-planes/SKILL.md`. Not needed to use the skill; open it only to check
where a claim or tag came from. Sections are grouped by the file that cites them.

## `references/clip-planes-and-precision.md`

- **[VRChat Camera Settings]** VRChat, "VRC Camera Settings", VRChat Creator Docs, 2025. https://creators.vrchat.com/worlds/udon/vrc-graphics/vrc-camera-settings/ — the site returned 403, so I read the raw Markdown at https://raw.githubusercontent.com/vrchat-community/creator-docs/main/Docs/docs/worlds/udon/vrc-graphics/vrc-camera-settings.md
- **[VRChat Scene Descriptor]** VRChat, "VRC Scene Descriptor", VRChat Creator Docs, n.d. https://creators.vrchat.com/worlds/components/vrc_scenedescriptor/ — read as raw Markdown from the creator-docs GitHub repo (the site returned 403).
- **[VRChat First World]** VRChat, "Creating Your First World", VRChat Creator Docs, n.d. https://github.com/vrchat-community/creator-docs/blob/main/Docs/docs/worlds/creating-your-first-world.md — read as raw Markdown.
- **[VRChat Mirror Reflection]** VRChat, "VRC Mirror Reflection", VRChat Creator Docs, n.d. https://raw.githubusercontent.com/vrchat-community/creator-docs/main/Docs/docs/worlds/components/vrc_mirrorreflection.md — downloaded with curl; I read only the lines mentioning clip, camera and layer.
- **[VRChat Dev Update 2022-08-03]** Tupper (VRChat), "Developer Update - 3 August 2022", VRChat Ask Forum, 2022. https://ask.vrchat.com/t/developer-update-3-august-2022/11265 — read via the Discourse API ("Viewpoint Near-Clip" section).
- **[VRChat 2024.1.1]** VRChat, "VRChat 2024.1.1" release notes, docs.vrchat.com, 2024. https://docs.vrchat.com/docs/vrchat-202411 — read in full.
- **[VRChat 2025.4.2]** VRChat, "VRChat 2025.4.2 (Open Beta)" release notes, docs.vrchat.com, 2025. https://docs.vrchat.com/docs/vrchat-202542-openbeta — read in full.
- **[WildCat Canny 2025]** -WildCat- (replies by hdorriker, -AKU-), "'Dynamic' Forced Camera Near Distance not working as intended", VRChat Feedback (Canny), 2025. https://feedback.vrchat.com/bug-reports/p/dynamic-forced-camera-near-distance-not-working-as-intended — read the page.
- **[hdorriker Canny 2025]** hdorriker (reply by Ericbazinga), "Forced Near Clip Persistence should be overridable by worlds.", VRChat Feedback (Canny), 2025. https://feedback.vrchat.com/bug-reports/p/forced-near-clip-persistence-should-be-overridable-by-worlds — read the page. The tag [Ericbazinga in hdorriker Canny 2025] refers to Ericbazinga's reply on this page.
- **[Mr. Imagination Canny 2024]** Mr. Imagination (reply by Kiro, VRChat), "Physbones Jitter With Imobile Type World", VRChat Feedback (Canny), 2024. https://feedback.vrchat.com/bug-reports/p/physbones-jitter-with-imobile-type-world — read the page.
- **[VRChat Ask 2024]** CGInteract, JessicaOnMain, Salbug et al., "Why does VRChat break at far enough distances in big worlds", VRChat Ask Forum, 2024. https://ask.vrchat.com/t/why-does-vrchat-break-at-far-enough-distances-in-big-worlds/23544 — read via the Discourse API.
- **[VRChat Wikidot Render Distance]** VRChat's Unofficial Wiki contributors, "Render Distance", vrchat.wikidot.com, n.d. (old; it cites the Unity 2018.1 docs). http://vrchat.wikidot.com/worlds:guides:render-distance — read the page.
- **[Reed 2015]** Nathan Reed, "Depth Precision Visualized", NVIDIA Developer, 2015. https://developer.nvidia.com/content/depth-precision-visualized — read in full.
- **[Unity Platform Differences]** Unity Technologies, "Writing shaders for different graphics APIs" (section "The Depth (Z) direction in Shaders"), Unity Manual 2022.3. https://docs.unity3d.com/2022.3/Documentation/Manual/SL-PlatformDifferences.html — read the page.
- **[Unity Shadow Distance]** Unity Technologies, "Shadow Distance", Unity Manual 2022.3. https://docs.unity3d.com/2022.3/Documentation/Manual/shadow-distance.html — read the page.
- **[Unity RenderToCubemap]** Unity Technologies, "Camera.RenderToCubemap", Unity Scripting API 2022.3. https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Camera.RenderToCubemap.html — read the page, including the `ConvertToEquirect` example.
- **[Unity 3D Skybox]** Unity Technologies, "3D Skybox", UniversalRenderingExamples wiki, GitHub, n.d. https://github.com/Unity-Technologies/UniversalRenderingExamples/wiki/3D-Skybox — read the page.
- **[Dawson 2012]** Bruce Dawson, "Don't Store That in a Float", Random ASCII, 2012. https://randomascii.wordpress.com/2012/02/13/dont-store-that-in-a-float/ — read the page, including the precision-by-length table.
- **[KitKat4191 JetSim FO]** KitKat4191, "JetSim - Floating Origin" README, GitHub, n.d. https://github.com/KitKat4191/JetSim-FloatingOrigin — read the README via the GitHub API.
- **[in-house]** Kit knowledge notes in `.omp/knowledge/notes/`. Read in full: `vrchat-camera-clip-planes-and-far-cut-fog-math` and `fog-must-be-radial-and-shader-driven-for-mirrors`. Read through grep excerpts and `.omp/knowledge/INDEX.md` summaries: `blockout-scale-and-multi-area-layout`, `build-scripted-joints-as-overlaps-not-flush-contacts`, `terrain-trees-refresh-popping-and-night-emission`, `budget-visible-triangles-per-viewpoint`, `tree-impostor-capture-pipeline`, `hdri-skybox-import-resolution-and-softness`, `match-skybox-sun-azimuth-to-the-baked-sun`, `skybox-swap-and-hdri-sun-alignment`, `bakery-needs-a-sky-light-for-ambient`, `moonlit-fog-night-scene-recipe`, `interior-reads-cozy-only-if-darker-outside`, `scene-view-far-clip-hides-distant-objects` and `measure-sightlines-by-raycasting-the-route`. Also the tolerance model in `.omp/unity-package/com.awdk.agenttools/Editor/ZFightRender.cs`, and user reports (the ~500 m limit, a 1000 m far clip on a shipped flying world, private rooms ≥ 200 m away).
- **[in-house, measured]** Throwaway C# run through the Unity MCP `execute_code` in Unity 2022.3.22f1 on D3D11, 2026-10-10: depth formats, depth-separation sweeps (§2.3), skybox overpaint sweeps (§2.5) and close-up jitter (§3.2). No assets or scene changes were saved.

## `SKILL.md`

Tags removed from the skill's text; full entries are under `references/clip-planes-and-precision.md` above:
- [Dawson 2012]
- [KitKat4191 JetSim FO]
- [Mr. Imagination Canny 2024]
- [Reed 2015]
- [Unity Platform Differences]
- [Unity RenderToCubemap]
- [VRChat Camera Settings]
- [VRChat Dev Update 2022-08-03]
- [VRChat Scene Descriptor]
- [WildCat Canny 2025]
- [hdorriker Canny 2025]
