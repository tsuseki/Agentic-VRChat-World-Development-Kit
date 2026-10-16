using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Rendering;

namespace AWDK.AgentTools
{
    /// <summary>Depth precision model behind <see cref="ZFightRender.Tolerance"/>.</summary>
    public enum ZDepthFormat
    {
        /// <summary>
        /// VRChat PC (Unity 2022.3, D3D11/12, Metal): reversed-Z with a 32-bit float depth buffer, measured
        /// D32_SFloat even when 24 bits are requested. Precision does not depend on the near clip.
        /// </summary>
        Float32ReversedZ,
        /// <summary>24-bit fixed-point depth (conservative model for Android/Quest and other non-reversed platforms).</summary>
        Fixed24,
    }

    /// <summary>Per-shot result of <see cref="ZFightRender"/>.</summary>
    public sealed class ZFightShotResult
    {
        public string Name, MaskPath;
        public int Width, Height;
        /// <summary>Pixels where another renderer's surface lies within the tie tolerance of the visible one.</summary>
        public int ZFightPixels;
        /// <summary>Bounding box of flagged pixels (y from the top); width -1 when none.</summary>
        public RectInt Box = new RectInt(-1, -1, -1, -1);
        /// <summary>Renderer pairs by flagged pixel count, largest first.</summary>
        public List<(string PathA, string PathB, int Pixels)> Pairs = new List<(string, string, int)>();
        /// <summary>Tie tolerance in metres at 20 m eye depth from this shot's camera position.</summary>
        public float Tolerance20m;
        public float Fraction => Width * Height == 0 ? 0 : (float)ZFightPixels / (Width * Height);
    }

    /// <summary>
    /// Image-based z-fighting detector. Read-only (uses the persistent __CapCam__; never changes
    /// renderers, materials or settings).
    ///
    /// For each shot it draws every visible opaque MeshRenderer off-screen in a flat per-renderer ID
    /// colour (frustum- and LOD-culled like the real camera, each renderer's own cull mode):
    ///   pass 1: the visible surface per pixel (ID + linear eye depth), normal depth test;
    ///   pass 2: every fragment of a renderer other than the visible one at that pixel whose eye depth
    ///           lies within the tie tolerance of the visible surface is flagged with its ID.
    /// A flagged pixel is a z-fight between the two renderers as seen from this viewpoint.
    ///
    /// Tie tolerance at eye depth d, with C the largest per-axis |coordinate| of the shot's camera:
    ///   tol = max(<see cref="MinTolerance"/>, <see cref="DepthSteps"/> * e),
    ///   <see cref="ZDepthFormat.Float32ReversedZ"/> (default, VRChat PC): e = 2^-24 * C + 2^-23 * d
    ///     (float32 world-position rounding plus float reversed-Z depth precision, independent of the
    ///     near clip; bounds every separation measured on 2022.3 D3D11, e.g. 4.3 µm at 100 m from the
    ///     origin, 67 µm at 100 m with the camera at x = z = 1000). Within 200 m of the origin and 100 m
    ///     of view distance the 0.05 mm floor governs: only exactly or effectively coplanar pairs fight.
    ///   <see cref="ZDepthFormat.Fixed24"/>: e = 2^-24 * C + d² / (<see cref="NearClip"/> * 2^24),
    ///     about 0.2 mm at 4 m and 4.8 mm at 20 m with near 0.01.
    ///
    /// Why not compare renders at nudged near/far planes: measured on 2022.3 (D3D11), clip-plane
    /// variants of an exactly coplanar pair change only ~0.2 % of the overlap pixels in a still frame,
    /// because the tie is decided by a systematic rounding bias, not noise. Reversing the draw order
    /// flips even fewer. The tolerance pass flags the whole overlap.
    ///
    /// Writes &lt;name&gt;_zmask.png per shot: the normal camera render darkened, flagged pixels magenta.
    /// Not covered: SkinnedMeshRenderers, terrain, particles, transparent queues (&gt; 2500); alpha-cutout
    /// materials are drawn solid; overlaps inside one renderer (same ID) are invisible to this check
    /// (use ZFightScan with includeSelf).
    /// </summary>
    public static class ZFightRender
    {
        public const string Kind = "ZFightRender";
        public const string ShaderName = "Hidden/AWDK/ZTieId";
        /// <summary>Depth precision model; default VRChat PC (float32 reversed-Z).</summary>
        public static ZDepthFormat DepthFormat = ZDepthFormat.Float32ReversedZ;
        /// <summary>
        /// Near clip plane in metres the <see cref="ZDepthFormat.Fixed24"/> model assumes (VRChat clamps the
        /// runtime near to 0.001-0.05 m; the Reference Camera minimum is 0.01). Float32ReversedZ ignores it.
        /// </summary>
        public static float NearClip = 0.01f;
        /// <summary>Safety factor: multiples of the precision step within which two surfaces count as tied.</summary>
        public static float DepthSteps = 2f;
        /// <summary>Lower bound of the tie tolerance in metres (effectively-coplanar floor).</summary>
        public static float MinTolerance = 0.00005f;
        const float Pow2Minus24 = 1f / 16777216f;
        /// <summary>Renderer pairs listed per shot.</summary>
        public static int MaxPairsPerShot = 8;

        static List<ZFightShotResult> last;
        static Material idMat;

        /// <summary>Starts a time-sliced render pass. Poll <see cref="Status"/> until the report ends with "COMPLETE".</summary>
        public static string Start(string outDir, string shotsJson)
        {
            string dir; Shot[] shots;
            try { dir = Util.OutDir(outDir); shots = Util.ParseShots(shotsJson); IdMaterial(); }
            catch (Exception e) { return "ERROR " + e.Message; }
            JobRunner.Start(Kind, job => Run(job, dir, shots));
            return string.Format(Util.Inv, "STARTED ZFightRender shots={0} out={1}; poll ZFightRender.Status()", shots.Length, dir);
        }

        public static string Status() => JobRunner.Status(Kind);

        /// <summary>Runs to completion on the calling thread (tests / scripts).</summary>
        public static string RunBlocking(string outDir, string shotsJson, double maxSeconds = 120)
        {
            string dir; Shot[] shots;
            try { dir = Util.OutDir(outDir); shots = Util.ParseShots(shotsJson); IdMaterial(); }
            catch (Exception e) { return "ERROR " + e.Message; }
            return JobRunner.RunBlocking(JobRunner.Create(Kind, job => Run(job, dir, shots)), maxSeconds);
        }

        public static IReadOnlyList<ZFightShotResult> LastResults => last ?? (IReadOnlyList<ZFightShotResult>)Array.Empty<ZFightShotResult>();

        /// <summary>
        /// Tie tolerance in metres at eye depth <paramref name="depth"/>, for a camera whose largest per-axis
        /// |world coordinate| is <paramref name="cameraCoord"/>, under <see cref="DepthFormat"/>.
        /// </summary>
        public static float Tolerance(float depth, float cameraCoord = 0f)
        {
            Coefficients(cameraCoord, out float a, out float b, out float k);
            return Mathf.Max(MinTolerance, a + b * depth + k * depth * depth);
        }

        /// <summary>tol = max(MinTolerance, a + b·d + k·d²); the shader evaluates the same polynomial.</summary>
        static void Coefficients(float cameraCoord, out float a, out float b, out float k)
        {
            a = DepthSteps * Mathf.Abs(cameraCoord) * Pow2Minus24;
            if (DepthFormat == ZDepthFormat.Fixed24) { b = 0f; k = DepthSteps * Pow2Minus24 / NearClip; }
            else { b = DepthSteps * 2f * Pow2Minus24; k = 0f; }
        }

        static float CameraCoord(Vector3 p) => Mathf.Max(Mathf.Abs(p.x), Mathf.Max(Mathf.Abs(p.y), Mathf.Abs(p.z)));

        /// <summary>ID colour of renderer index i (0 is background).</summary>
        public static Color32 IdColor(int index)
        {
            int id = index + 1;
            return new Color32((byte)(id & 255), (byte)((id >> 8) & 255), (byte)((id >> 16) & 255), 255);
        }

        public static int IdOf(Color32 c) => c.r | (c.g << 8) | (c.b << 16);

        /// <summary>
        /// Marks pixels where both ID images show a renderer (non-zero ID) and the IDs differ: here the
        /// visible-surface IDs against the tie-pass IDs. <paramref name="mask"/> accumulates;
        /// <paramref name="pairs"/> (optional) counts newly marked pixels per ID pair, keyed
        /// (min &lt;&lt; 32 | max). Returns the number of differing pixels in this comparison.
        /// </summary>
        public static int CompareIds(Color32[] a, Color32[] b, bool[] mask, Dictionary<long, int> pairs)
        {
            if (a.Length != b.Length || a.Length != mask.Length) throw new ArgumentException("size mismatch");
            int differ = 0;
            for (int i = 0; i < a.Length; i++)
            {
                int ia = IdOf(a[i]), ib = IdOf(b[i]);
                if (ia == 0 || ib == 0 || ia == ib) continue;
                differ++;
                if (mask[i]) continue;
                mask[i] = true;
                if (pairs != null)
                {
                    long key = ia < ib ? ((long)ia << 32) | (uint)ib : ((long)ib << 32) | (uint)ia;
                    pairs.TryGetValue(key, out int n);
                    pairs[key] = n + 1;
                }
            }
            return differ;
        }

        /// <summary>Mask image: base darkened to 35 % grey, marked pixels magenta.</summary>
        public static Color32[] MaskImage(Color32[] baseImg, bool[] mask)
        {
            var o = new Color32[baseImg.Length];
            for (int i = 0; i < o.Length; i++)
            {
                if (mask[i]) { o[i] = new Color32(255, 0, 255, 255); continue; }
                var p = baseImg[i];
                byte g = (byte)((p.r * 0.30f + p.g * 0.59f + p.b * 0.11f) * 0.35f);
                o[i] = new Color32(g, g, g, 255);
            }
            return o;
        }

        static Material IdMaterial()
        {
            if (idMat != null) return idMat;
            var sh = Shader.Find(ShaderName);
            if (sh == null) throw new InvalidOperationException("shader " + ShaderName + " not found (package not imported?)");
            idMat = new Material(sh) { hideFlags = HideFlags.HideAndDontSave };
            return idMat;
        }

        struct Draw { public Renderer R; public int Submesh; public int Index; public float Cull; }

        static IEnumerator Run(AgentJob job, string dir, Shot[] shots)
        {
            var results = new List<ZFightShotResult>();
            last = results;
            var cam = Util.CapCam();

            // Candidate renderers, indexed for ID colours.
            var renderers = new List<MeshRenderer>();
            foreach (var root in Util.ResolveRoots(null))
                foreach (var r in root.GetComponentsInChildren<MeshRenderer>(false))
                    if (r.enabled && !r.forceRenderingOff && r.shadowCastingMode != ShadowCastingMode.ShadowsOnly && !Util.IsEditorOnly(r.transform))
                        renderers.Add(r);
            yield return null;

            for (int si = 0; si < shots.Length; si++)
            {
                var s = shots[si];
                job.Progress = string.Format(Util.Inv, "shot {0}/{1} {2}", si + 1, shots.Length, s.name);
                var res = new ZFightShotResult { Name = s.name, Width = s.w, Height = s.h, Tolerance20m = Tolerance(20f, CameraCoord(s.Pos)) };

                Util.Aim(cam, s);
                var draws = VisibleDraws(cam, renderers);
                RenderTies(cam, s, draws, out var visibleIds, out var tieIds);
                yield return null;
                var mask = new bool[visibleIds.Length];
                var pairCounts = new Dictionary<long, int>();
                res.ZFightPixels = CompareIds(visibleIds, tieIds, mask, pairCounts);

                int x0 = int.MaxValue, y0 = int.MaxValue, x1 = -1, y1 = -1;
                for (int i = 0; i < mask.Length; i++)
                {
                    if (!mask[i]) continue;
                    int x = i % s.w, y = s.h - 1 - i / s.w;
                    x0 = Math.Min(x0, x); x1 = Math.Max(x1, x);
                    y0 = Math.Min(y0, y); y1 = Math.Max(y1, y);
                }
                if (res.ZFightPixels > 0) res.Box = new RectInt(x0, y0, x1 - x0, y1 - y0);
                var sorted = new List<KeyValuePair<long, int>>(pairCounts);
                sorted.Sort((a, b) => b.Value.CompareTo(a.Value));
                foreach (var kv in sorted)
                {
                    var ra = renderers[(int)(kv.Key >> 32) - 1];
                    var rb = renderers[(int)(kv.Key & 0xffffffff) - 1];
                    res.Pairs.Add((ra != null ? Util.PathOf(ra.transform) : "<destroyed>", rb != null ? Util.PathOf(rb.transform) : "<destroyed>", kv.Value));
                }

                var visual = RenderVisual(cam, s);
                var tex = new Texture2D(s.w, s.h, TextureFormat.RGBA32, false, false);
                try
                {
                    tex.SetPixels32(MaskImage(visual, mask));
                    tex.Apply(false);
                    res.MaskPath = Path.Combine(dir, s.name + "_zmask.png");
                    File.WriteAllBytes(res.MaskPath, tex.EncodeToPNG());
                }
                finally { UnityEngine.Object.DestroyImmediate(tex); }
                results.Add(res);
                yield return null;
            }

            var sb = new StringBuilder();
            sb.AppendLine(string.Format(Util.Inv, "ZFIGHT render: scenes={0} renderers={1} tolerance: depth={2} nearClip={3} depthSteps={4} min={5:0.###} mm -> {6:0.###} mm at 4 m, {7:0.###} mm at 20 m (camera at origin)",
                Util.SceneNames(), renderers.Count, DepthFormat, NearClip, DepthSteps, MinTolerance * 1000f, Tolerance(4f) * 1000f, Tolerance(20f) * 1000f));
            long total = 0;
            foreach (var r in results)
            {
                total += r.ZFightPixels;
                sb.AppendLine(string.Format(Util.Inv, "{0}: {1}x{2} zfightPixels={3} ({4:0.###}%) box={5} tol@20m={6:0.###} mm mask={7}",
                    r.Name, r.Width, r.Height, r.ZFightPixels, r.Fraction * 100f,
                    r.ZFightPixels > 0 ? string.Format(Util.Inv, "x{0}-{1},y{2}-{3}", r.Box.xMin, r.Box.xMax, r.Box.yMin, r.Box.yMax) : "-",
                    r.Tolerance20m * 1000f, r.MaskPath));
                for (int i = 0; i < r.Pairs.Count && i < MaxPairsPerShot; i++)
                    sb.AppendLine(string.Format(Util.Inv, "    {0} px  {1}  <->  {2}", r.Pairs[i].Pixels, r.Pairs[i].PathA, r.Pairs[i].PathB));
                if (r.Pairs.Count > MaxPairsPerShot) sb.AppendLine("    ... " + (r.Pairs.Count - MaxPairsPerShot) + " more pairs");
            }
            sb.Append(string.Format(Util.Inv, "SHOTS={0} ZFIGHT_PIXELS={1} COMPLETE", results.Count, total));
            job.Result = sb.ToString();
        }

        /// <summary>Opaque submeshes the camera would draw: in the frustum, culling mask, current LOD.</summary>
        static List<Draw> VisibleDraws(Camera cam, List<MeshRenderer> renderers)
        {
            var planes = GeometryUtility.CalculateFrustumPlanes(cam);
            var lodCache = new Dictionary<LODGroup, int>();
            var draws = new List<Draw>();
            for (int i = 0; i < renderers.Count; i++)
            {
                var r = renderers[i];
                if (r == null || !r.gameObject.activeInHierarchy || (cam.cullingMask & (1 << r.gameObject.layer)) == 0) continue;
                var mf = r.GetComponent<MeshFilter>();
                if (mf == null || mf.sharedMesh == null) continue;
                if (!GeometryUtility.TestPlanesAABB(planes, r.bounds)) continue;
                if (!LodVisible(cam, r, lodCache)) continue;
                var mats = r.sharedMaterials;
                for (int sm = 0; sm < mf.sharedMesh.subMeshCount; sm++)
                {
                    var m = mats.Length == 0 ? null : mats[Math.Min(sm, mats.Length - 1)];
                    if (m != null && m.renderQueue > 2500) continue;
                    if (mf.sharedMesh.GetTopology(sm) != MeshTopology.Triangles) continue;
                    float cull = 2f; // Back
                    if (m != null)
                    {
                        if (m.HasProperty("_Cull")) cull = m.GetFloat("_Cull");
                        else if (m.HasProperty("_CullMode")) cull = m.GetFloat("_CullMode");
                    }
                    draws.Add(new Draw { R = r, Submesh = sm, Index = i, Cull = cull });
                }
            }
            return draws;
        }

        static bool LodVisible(Camera cam, Renderer r, Dictionary<LODGroup, int> cache)
        {
            var group = r.GetComponentInParent<LODGroup>();
            if (group == null || !group.enabled) return true;
            var lods = group.GetLODs();
            int mine = -1;
            for (int i = 0; i < lods.Length && mine < 0; i++)
                if (lods[i].renderers != null && Array.IndexOf(lods[i].renderers, r) >= 0) mine = i;
            if (mine < 0) return true;
            if (!cache.TryGetValue(group, out int active))
            {
                var t = group.transform;
                var s = t.lossyScale;
                float size = group.size * Mathf.Max(Mathf.Abs(s.x), Mathf.Max(Mathf.Abs(s.y), Mathf.Abs(s.z)));
                float dist = Vector3.Distance(cam.transform.position, t.TransformPoint(group.localReferencePoint));
                float rel = size / (2f * Mathf.Max(dist, 1e-4f) * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad)) * QualitySettings.lodBias;
                active = -1;
                for (int i = 0; i < lods.Length; i++)
                    if (rel >= lods[i].screenRelativeTransitionHeight) { active = i; break; }
                cache[group] = active;
            }
            return active == mine;
        }

        static void RenderTies(Camera cam, Shot s, List<Draw> draws, out Color32[] visibleIds, out Color32[] tieIds)
        {
            var mat = IdMaterial();
            var idRt = RenderTexture.GetTemporary(new RenderTextureDescriptor(s.w, s.h, RenderTextureFormat.ARGB32, 24) { sRGB = false, msaaSamples = 1 });
            var depthRt = RenderTexture.GetTemporary(new RenderTextureDescriptor(s.w, s.h, RenderTextureFormat.RFloat, 0) { msaaSamples = 1 });
            var tieRt = RenderTexture.GetTemporary(new RenderTextureDescriptor(s.w, s.h, RenderTextureFormat.ARGB32, 0) { sRGB = false, msaaSamples = 1 });
            var cmd = new CommandBuffer { name = "ZFightRender" };
            try
            {
                var proj = Matrix4x4.Perspective(s.fov, (float)s.w / s.h, s.near, s.far);
                cmd.SetRenderTarget(new RenderTargetIdentifier[] { idRt, depthRt }, idRt.depthBuffer);
                cmd.ClearRenderTarget(true, true, Color.clear);
                cmd.SetViewProjectionMatrices(cam.worldToCameraMatrix, proj);
                foreach (var d in draws) Draw1(cmd, mat, d, 0);

                cmd.SetRenderTarget(tieRt);
                cmd.ClearRenderTarget(false, true, Color.clear);
                cmd.SetGlobalTexture("_ZTieIds", idRt);
                cmd.SetGlobalTexture("_ZTieDepth", depthRt);
                Coefficients(CameraCoord(s.Pos), out float a, out float b, out float k);
                cmd.SetGlobalFloat("_ZTieA", a);
                cmd.SetGlobalFloat("_ZTieB", b);
                cmd.SetGlobalFloat("_ZTieK", k);
                cmd.SetGlobalFloat("_ZTieMinTol", MinTolerance);
                cmd.SetViewProjectionMatrices(cam.worldToCameraMatrix, proj);
                foreach (var d in draws) Draw1(cmd, mat, d, 1);
                Graphics.ExecuteCommandBuffer(cmd);

                visibleIds = Read(idRt);
                tieIds = Read(tieRt);
            }
            finally
            {
                cmd.Release();
                RenderTexture.ReleaseTemporary(idRt);
                RenderTexture.ReleaseTemporary(depthRt);
                RenderTexture.ReleaseTemporary(tieRt);
            }
        }

        static void Draw1(CommandBuffer cmd, Material mat, Draw d, int pass)
        {
            if (d.R == null) return;
            var c = IdColor(d.Index);
            cmd.SetGlobalVector("_ZTieId", new Vector4(c.r / 255f, c.g / 255f, c.b / 255f, 1f));
            cmd.SetGlobalFloat("_ZTieCull", d.Cull);
            cmd.DrawRenderer(d.R, mat, d.Submesh, pass);
        }

        static Color32[] Read(RenderTexture rt)
        {
            var tex = Util.ReadBack(rt);
            try { return tex.GetPixels32(); }
            finally { UnityEngine.Object.DestroyImmediate(tex); }
        }

        static Color32[] RenderVisual(Camera cam, Shot s)
        {
            var rt = RenderTexture.GetTemporary(new RenderTextureDescriptor(s.w, s.h, RenderTextureFormat.ARGB32, 24) { sRGB = true, msaaSamples = 1 });
            try
            {
                Util.Aim(cam, s);
                cam.allowMSAA = false;
                cam.clearFlags = CameraClearFlags.Skybox;
                cam.targetTexture = rt;
                cam.Render();
                var tex = Util.ReadBack(rt);
                var px = tex.GetPixels32();
                UnityEngine.Object.DestroyImmediate(tex);
                return px;
            }
            finally
            {
                cam.targetTexture = null;
                RenderTexture.ReleaseTemporary(rt);
            }
        }
    }
}
