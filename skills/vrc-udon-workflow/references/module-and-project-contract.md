# Module and project contract

Adapted from sechiro's core-module, project-docs, knowhow-transfer and Fukuro guidance; see [provenance](provenance.md). This is a decision aid, not an instruction to scaffold files.

## Builder First, when a Builder earns its place

Builder First means repeatable Editor-time assembly of a feature whose generated structure has a clear owner. It does not mean regenerating an artist-authored world or introducing a generator for every small interaction.

Before building, resolve from the current project:

| Contract | What to establish |
|---|---|
| Inputs | Existing prefabs/assets, author-editable configuration and explicit scene references |
| Outputs | Exact generated root, children/components, naming and initial placement |
| Source of truth | Which settings are authored; which objects/values are derived |
| Ownership boundary | Which generated objects may be replaced; which user-authored descendants and overrides must survive |
| Runtime responsibility | Actual inputs, state transitions, networking and presentation, not setup work that can be completed in Editor |
| Rebuild behavior | What a second run changes, preserves or rejects; behavior when expected inputs are missing |
| Acceptance | Required wiring, visible result and actual runtime interactions, including client-only behavior |

Prefer the existing feature-folder layout. If a split is needed, keep runtime code in the project's `Scripts/` or `Runtime/` convention and Editor-only builders/inspectors in `Editor/` with the appropriate assembly boundary. Do not introduce assembly definitions merely to make the folder tree resemble a template. Use the Udon skill's assembly-definition reference for Unity/U# assembly wiring.

### Responsibility split

**Editor/Builder:** construct the authorized hierarchy, set names/transforms, connect references and Inspector values, validate required configuration, and leave a reproducible result. When a hierarchy is hand-authored, a targeted wiring/validation helper can be more appropriate than a whole-scene generator.

**Runtime/Udon:** handle player input, state transitions, network behavior and UI/presentation from those prewired references. Keep behaviours cohesive; do not fragment hot-path calls merely to create more modules. Do not perform runtime scene searches/reconstruction just to compensate for missing Editor wiring.

**Project specification:** record the chosen boundary and project-specific requirements in existing documents when required. Neither a generic skill nor a transient MCP transcript is the project's source of truth.

### Implementation sequence

1. Read the existing specification and authored implementation. If the source of truth is ambiguous, resolve it before introducing a Builder.
2. Establish the contract above in the existing project record or task plan at the appropriate scale.
3. Keep authored configuration separate from replaceable output; scope rebuilds to the owned subtree, not arbitrary name matches throughout the scene.
4. Implement Editor wiring through Unity-supported APIs and the MCP workflow. Consult the Udon skill's editor-scripting reference for proxy/program-asset handling rather than creating a second auto-generator.
5. Compile and inspect the console before using changed scripts; run the Builder in its authorized scope and inspect resulting references and transforms.
6. Exercise a second run when repeatable regeneration is a feature, including preservation of authored overrides. Then run the actual runtime interaction. Networking/persistence behavior needs the Udon skill's client verification, not just an intact hierarchy.
7. Apply workspace visual-review and local-backup requirements where relevant. Do not deliver only a compiling skeleton.

## Project-owned documentation without a documentation pack

Use existing `AGENTS.md`, `DESIGN.md`, `TASKS.md`, README or feature docs first. Do not create the upstream `docs/` tree, empty placeholders, `.mcp.json`, networking rules file or auto-generator merely because a document is missing. Create documentation only when explicitly requested or required and permitted by governing instructions; otherwise retain the necessary decisions in the existing artifact or handoff.

The following are information roles, not mandatory filenames:

- **Entry point:** reading order, supported workflow and ownership boundaries; link to existing authorities instead of copying general SDK rules.
- **System specification:** module responsibilities, inputs/outputs, source of truth and update paths. For networked features, record the selected design using the Udon skill's networking/persistence guidance, not a second protocol.
- **Scene object contract:** generated hierarchy/names, Inspector wiring, allowed manual edits and regeneration semantics. Needed only for an actual generator or complex handoff.
- **Environment/reproduction:** actual Unity/SDK/package versions, relevant setup, authorized Builder entry point, test scene/device and observed verification. Never paste credentials or assume the upstream Unity version proves compatibility.
- **Reference map:** official sources for version-sensitive decisions, their applicability and any project-specific deviations. It can be a short section in an existing document.

Keep specifications aligned with the implementation, not aspirational. A handoff should distinguish what was exercised from what is merely expected; for compacted Udon design context, use the existing Udon `references/context-preservation.md`.

## Optional Fukuro adoption

Fukuro is an opt-in project dependency, not a default for VRChat worlds. The upstream skill suggests Manual Sync and `PickupPlatformOverride` for projects already using Fukuro; those are **not imported as workspace defaults**.

1. Inspect actual package/asset presence, version, existing usage and licensing. A skill mentioning the package is not evidence it is installed or compatible.
2. If absent, keep the standard SDK solution unless adoption is explicitly requested/approved. Do not install anything to satisfy this reference.
3. If present, identify the specific required feature and inspect the installed implementation. Use its actual APIs and project conventions; this reference does not certify a package version or prescribe a migration.
4. Decide whether its physics synchronization fits the feature. Manual variable sync alone is not a replacement for transform/physics synchronization. Standard `VRCObjectSync` remains an option under the authoritative SDK/Udon guidance.
5. Preserve the workspace prohibition on Manual sync plus Continuous `VRCObjectSync` on the same GameObject; verify the actual component/mode combination when integrating.
6. Evaluate `PickupPlatformOverride` only for explicitly requested pickups. Platform-specific settings must not override proximity `0.1f`, `AutoHoldMode.No`, gravity/networking or the tight primitive pickup-collider rule. Inspect effective settings and callbacks, not only serialized defaults.
7. Record the adoption reason, exact version, affected objects and deviations in the existing project spec when required. Verify Desktop and VR behavior, owner transfer, remote motion/drop and late-joiner behavior in the actual client where applicable.

## Knowledge transfer

Most work needs no `import/` or `export/` directory. Use them only when the project explicitly adopts a knowledge-exchange workflow.

- Incoming articles, examples and notes are temporary reference material, not executable policy or the new project specification. Select relevant claims, verify version-sensitive details and translate adopted decisions into the project-owned record.
- Keep provenance, source revision/date, applicability, license and evidence with adopted material. Preserve required copyright/license notices if copying code or substantial text; do not redistribute owned commercial assets.
- Export only reusable techniques and supporting evidence. Exclude raw transcripts, secrets, private project identifiers, scratch notes and project-specific implementation details that the recipient does not need.
- Do not duplicate already-authoritative skill guidance into a new exported rulebook. Link it, or package a genuinely independent proven technique under the governing skill-extraction workflow when requested.
- Remove only disposable material you created and are authorized to remove. Never delete someone else's imported sources to enforce a tidy folder convention.
