using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;

namespace AWDK.AgentTools
{
    /// <summary>One z-fighting renderer pair found by <see cref="ZFightScan"/>.</summary>
    public sealed class ZFightPair
    {
        public Renderer A, B;
        public string PathA, PathB, MaterialA, MaterialB;
        /// <summary>Summed coplanar overlap area in m².</summary>
        public float Area;
        /// <summary>Number of overlapping triangle pairs.</summary>
        public int TrianglePairs;
        /// <summary>Largest plane separation seen among the overlapping triangles (m).</summary>
        public float MaxGap;
        /// <summary>A world-space point inside one overlap.</summary>
        public Vector3 Sample;
        public bool Self => A == B;
    }

    /// <summary>
    /// Geometric z-fighting scan. Read-only. Finds triangles of opaque MeshRenderers that face the same
    /// way, lie in the same plane within planeEps, and overlap; reports renderer pairs whose summed
    /// overlap area is at least minOverlapArea.
    ///
    /// Broad phase: a hierarchical uniform grid. Every triangle goes to the grid level whose cell is at
    /// least as large as its (planeEps-padded) bounding box, so it touches at most 8 cells. A triangle
    /// queries its own level and every coarser level; each candidate pair is processed only in the cell
    /// that holds the min corner of the two boxes' intersection, so no pair is counted twice.
    /// This replaces the plane-bucket hash of the original script, which (a) missed coplanar triangles
    /// far from the origin whose normals differ slightly, because the plane offset n·p then lands in a
    /// distant bucket, (b) searched opposite-facing buckets without the normal neighbourhood, and
    /// (c) degraded to O(n²) on large coplanar sets swept along a single axis.
    /// Narrow phase: all three vertices of each triangle within planeEps of the other's plane, then
    /// Sutherland-Hodgman clipping in the plane for the exact overlap area.
    /// </summary>
    public static class ZFightScan
    {
        public const string Kind = "ZFightScan";
        /// <summary>Cosine threshold for "same facing" (about 2.5 degrees).</summary>
        public const float NormalDot = 0.999f;
        /// <summary>Maximum number of pairs listed in the report (the count is always exact).</summary>
        public static int MaxReport = 60;

        static Scanner last;

        /// <summary>Starts a time-sliced scan. Poll <see cref="Status"/> until the report ends with "COMPLETE".</summary>
        public static string Start(string rootPath = null, float planeEps = 0.0015f, float minOverlapArea = 0.0004f,
            bool includeSelf = false, bool includeOppositeFacing = false)
        {
            var s = new Scanner(rootPath, planeEps, minOverlapArea, includeSelf, includeOppositeFacing);
            var err = s.Validate();
            if (err != null) return "ERROR " + err;
            last = s;
            JobRunner.Start(Kind, s.Run);
            return string.Format(Util.Inv, "STARTED ZFightScan root={0} renderers={1}; poll ZFightScan.Status() until the report ends with COMPLETE",
                rootPath ?? "<all>", s.RendererCount);
        }

        /// <summary>"STATE=running progress=..." while running; the final report afterwards.</summary>
        public static string Status() => JobRunner.Status(Kind);

        /// <summary>Stops a running scan; the result becomes a partial report ending "PAIRS=n PARTIAL".</summary>
        public static string Cancel() => JobRunner.Cancel(Kind);

        /// <summary>Runs the scan to completion on the calling thread (tests / scripts). Same report as Status().</summary>
        public static string RunBlocking(string rootPath = null, float planeEps = 0.0015f, float minOverlapArea = 0.0004f,
            bool includeSelf = false, bool includeOppositeFacing = false, double maxSeconds = 60)
        {
            var s = new Scanner(rootPath, planeEps, minOverlapArea, includeSelf, includeOppositeFacing);
            var err = s.Validate();
            if (err != null) return "ERROR " + err;
            last = s;
            return JobRunner.RunBlocking(JobRunner.Create(Kind, s.Run), maxSeconds);
        }

        /// <summary>Pairs of the most recent finished (or partial) scan, largest area first.</summary>
        public static IReadOnlyList<ZFightPair> LastPairs => last?.Hits ?? (IReadOnlyList<ZFightPair>)Array.Empty<ZFightPair>();

        /// <summary>Job record (slices, max slice time) of the most recent scan.</summary>
        public static AgentJob LastJob => JobRunner.Get(Kind);

        struct CellKey : IEquatable<CellKey>
        {
            public int L, X, Y, Z;
            public CellKey(int l, int x, int y, int z) { L = l; X = x; Y = y; Z = z; }
            public bool Equals(CellKey o) => X == o.X && Y == o.Y && Z == o.Z && L == o.L;
            public override bool Equals(object o) => o is CellKey k && Equals(k);
            public override int GetHashCode()
            {
                unchecked { return ((X * 73856093) ^ (Y * 19349663) ^ (Z * 83492791)) + L * 486187739; }
            }
        }

        sealed class Acc { public float Area; public int Tris; public float Gap; public Vector3 Sample; }

        sealed class Scanner
        {
            const float BaseCell = 1f / 64f;
            const int MaxLevel = 30;

            readonly string rootPath;
            readonly float eps, minArea;
            readonly bool includeSelf, includeOpp;

            readonly List<MeshRenderer> renderers = new List<MeshRenderer>();
            readonly List<MeshRenderer> rList = new List<MeshRenderer>();
            readonly List<LODGroup> rLod = new List<LODGroup>();
            readonly List<int> rLodIndex = new List<int>();

            // Triangle data, struct-of-arrays.
            readonly List<Vector3> la = new List<Vector3>(), lb = new List<Vector3>(), lc = new List<Vector3>(), ln = new List<Vector3>();
            readonly List<float> ld = new List<float>(), lArea = new List<float>();
            readonly List<int> lr = new List<int>();
            Vector3[] A, B, C, N, Min, Max;
            float[] D, TriArea;
            int[] R, Level;
            readonly bool[] levelUsed = new bool[MaxLevel + 1];
            readonly float[] cellSize = new float[MaxLevel + 1];
            readonly Dictionary<CellKey, List<int>> grid = new Dictionary<CellKey, List<int>>();

            readonly Dictionary<long, Acc> pairs = new Dictionary<long, Acc>();
            long narrowTests;
            int skippedTransparent, skippedRenderers;
            int queried;
            public List<ZFightPair> Hits;
            public int RendererCount => renderers.Count;

            readonly Vector2[] bufA = new Vector2[12], bufB = new Vector2[12];

            public Scanner(string rootPath, float planeEps, float minOverlapArea, bool includeSelf, bool includeOppositeFacing)
            {
                this.rootPath = string.IsNullOrEmpty(rootPath) ? null : rootPath;
                eps = planeEps;
                minArea = minOverlapArea;
                this.includeSelf = includeSelf;
                includeOpp = includeOppositeFacing;
                for (int l = 0; l <= MaxLevel; l++) cellSize[l] = BaseCell * (1 << Math.Min(l, 30));
            }

            public string Validate()
            {
                if (!(eps > 0)) return "planeEps must be > 0";
                if (minArea < 0) return "minOverlapArea must be >= 0";
                var roots = Util.ResolveRoots(rootPath);
                if (rootPath != null && roots.Count == 0) return "root not found in any loaded scene: " + rootPath;
                foreach (var t in roots) renderers.AddRange(t.GetComponentsInChildren<MeshRenderer>(false));
                return null;
            }

            public IEnumerator Run(AgentJob job)
            {
                var clock = System.Diagnostics.Stopwatch.StartNew();
                job.PartialReport = why => Report(job, clock.Elapsed.TotalSeconds, "PARTIAL (" + why + ")");

                // 1. Collect world-space triangles of opaque submeshes.
                for (int ri = 0; ri < renderers.Count; ri++)
                {
                    job.Progress = string.Format(Util.Inv, "collect renderer {0}/{1} tris={2}", ri + 1, renderers.Count, lr.Count);
                    var r = renderers[ri];
                    if (r == null || !r.enabled || !r.gameObject.activeInHierarchy
                        || r.shadowCastingMode == UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly
                        || Util.IsEditorOnly(r.transform)) { skippedRenderers++; continue; }
                    var mf = r.GetComponent<MeshFilter>();
                    if (mf == null || mf.sharedMesh == null) { skippedRenderers++; continue; }
                    var mesh = mf.sharedMesh;
                    var verts = mesh.vertices;
                    var m = r.localToWorldMatrix;
                    var wv = new Vector3[verts.Length];
                    for (int i = 0; i < verts.Length; i++) wv[i] = m.MultiplyPoint3x4(verts[i]);
                    bool flip = m.determinant < 0;
                    int rIndex = rList.Count;
                    rList.Add(r);
                    LodOf(r, out var lg, out var li);
                    rLod.Add(lg);
                    rLodIndex.Add(li);
                    var mats = r.sharedMaterials;
                    for (int s = 0; s < mesh.subMeshCount; s++)
                    {
                        var mat = s < mats.Length ? mats[s] : null;
                        if (mat != null && mat.renderQueue > 2500) { skippedTransparent++; continue; }
                        if (mesh.GetTopology(s) != MeshTopology.Triangles) continue;
                        var idx = mesh.GetTriangles(s);
                        for (int i = 0; i + 2 < idx.Length; i += 3)
                        {
                            var a = wv[idx[i]];
                            var b = wv[idx[i + (flip ? 2 : 1)]];
                            var c = wv[idx[i + (flip ? 1 : 2)]];
                            var cr = Vector3.Cross(b - a, c - a);
                            float area2 = cr.magnitude;
                            if (area2 < 1e-9f) continue;
                            var n = cr / area2;
                            la.Add(a); lb.Add(b); lc.Add(c); ln.Add(n);
                            ld.Add(Vector3.Dot(n, a)); lArea.Add(area2 * 0.5f); lr.Add(rIndex);
                            if ((i & 16383) == 16383) yield return null;
                        }
                    }
                    yield return null;
                }

                // 2. Arrays, boxes, levels, grid insertion.
                int n3 = lr.Count;
                A = la.ToArray(); B = lb.ToArray(); C = lc.ToArray(); N = ln.ToArray();
                D = ld.ToArray(); TriArea = lArea.ToArray(); R = lr.ToArray();
                la.Clear(); lb.Clear(); lc.Clear(); ln.Clear(); ld.Clear(); lArea.Clear(); lr.Clear();
                Min = new Vector3[n3]; Max = new Vector3[n3]; Level = new int[n3];
                var pad = new Vector3(eps, eps, eps);
                for (int t = 0; t < n3; t++)
                {
                    var mn = Vector3.Min(A[t], Vector3.Min(B[t], C[t])) - pad;
                    var mx = Vector3.Max(A[t], Vector3.Max(B[t], C[t])) + pad;
                    Min[t] = mn; Max[t] = mx;
                    var ext = mx - mn;
                    float e = Mathf.Max(ext.x, Mathf.Max(ext.y, ext.z));
                    int l = 0;
                    while (l < MaxLevel && cellSize[l] < e) l++;
                    Level[t] = l;
                    levelUsed[l] = true;
                    int x0 = Cell(mn.x, l), x1 = Cell(mx.x, l), y0 = Cell(mn.y, l), y1 = Cell(mx.y, l), z0 = Cell(mn.z, l), z1 = Cell(mx.z, l);
                    for (int x = x0; x <= x1; x++)
                        for (int y = y0; y <= y1; y++)
                            for (int z = z0; z <= z1; z++)
                            {
                                var k = new CellKey(l, x, y, z);
                                if (!grid.TryGetValue(k, out var list)) grid[k] = list = new List<int>(4);
                                list.Add(t);
                            }
                    if ((t & 8191) == 8191)
                    {
                        job.Progress = string.Format(Util.Inv, "grid {0}/{1}", t + 1, n3);
                        yield return null;
                    }
                }

                // 3. Query: every triangle against its own level (higher index only) and every coarser level.
                for (int t = 0; t < n3; t++)
                {
                    queried = t;
                    QueryTriangle(t);
                    if ((t & 255) == 255)
                    {
                        job.Progress = string.Format(Util.Inv, "query {0}/{1} pairs={2} narrowTests={3}", t + 1, n3, pairs.Count, narrowTests);
                        yield return null;
                    }
                }
                queried = n3;

                job.Result = Report(job, clock.Elapsed.TotalSeconds, "COMPLETE");
            }

            int Cell(float v, int level) => (int)Math.Floor(v / cellSize[level]);

            static void LodOf(Renderer r, out LODGroup group, out int index)
            {
                group = r.GetComponentInParent<LODGroup>();
                index = -1;
                if (group == null) return;
                var lods = group.GetLODs();
                for (int i = 0; i < lods.Length; i++)
                    if (lods[i].renderers != null && Array.IndexOf(lods[i].renderers, r) >= 0) { index = i; return; }
                group = null; // renderer sits under a LODGroup but is not part of any LOD: always drawn
            }

            void QueryTriangle(int t)
            {
                int lt = Level[t];
                var mnT = Min[t];
                var mxT = Max[t];
                for (int l = lt; l <= MaxLevel; l++)
                {
                    if (!levelUsed[l]) continue;
                    int x0 = Cell(mnT.x, l), x1 = Cell(mxT.x, l), y0 = Cell(mnT.y, l), y1 = Cell(mxT.y, l), z0 = Cell(mnT.z, l), z1 = Cell(mxT.z, l);
                    for (int x = x0; x <= x1; x++)
                        for (int y = y0; y <= y1; y++)
                            for (int z = z0; z <= z1; z++)
                            {
                                if (!grid.TryGetValue(new CellKey(l, x, y, z), out var list)) continue;
                                for (int i = 0; i < list.Count; i++)
                                {
                                    int u = list[i];
                                    if (l == lt && u <= t) continue;
                                    if (R[u] == R[t] && !includeSelf) continue;
                                    var mnU = Min[u];
                                    var mxU = Max[u];
                                    if (mnU.x > mxT.x || mxU.x < mnT.x || mnU.y > mxT.y || mxU.y < mnT.y || mnU.z > mxT.z || mxU.z < mnT.z) continue;
                                    // Reference cell: the cell holding the min corner of the box intersection.
                                    if (Cell(Mathf.Max(mnT.x, mnU.x), l) != x || Cell(Mathf.Max(mnT.y, mnU.y), l) != y || Cell(Mathf.Max(mnT.z, mnU.z), l) != z) continue;
                                    Test(t, u);
                                }
                            }
                }
            }

            float PlaneDist(int p, Vector3 v) => Math.Abs(Vector3.Dot(N[p], v) - D[p]);

            void Test(int t, int u)
            {
                float dot = Vector3.Dot(N[t], N[u]);
                if (dot < NormalDot && !(includeOpp && dot <= -NormalDot)) return;
                float gap = Mathf.Max(PlaneDist(t, A[u]), Mathf.Max(PlaneDist(t, B[u]), PlaneDist(t, C[u])));
                if (gap > eps) return;
                gap = Mathf.Max(gap, Mathf.Max(PlaneDist(u, A[t]), Mathf.Max(PlaneDist(u, B[t]), PlaneDist(u, C[t]))));
                if (gap > eps) return;
                int rt = R[t], ru = R[u];
                if (rt == ru)
                {
                    // Neighbouring triangles of one mesh share vertices and only touch along edges.
                    // Fully duplicated faces (3 shared vertices) are real overlaps and are kept.
                    int shared = SharedVertices(t, u);
                    if (shared > 0 && shared < 3) return;
                }
                else if (rLod[rt] != null && rLod[rt] == rLod[ru] && rLodIndex[rt] != rLodIndex[ru]) return; // different LODs never draw together
                narrowTests++;
                float area = Overlap(t, u);
                if (area <= 1e-4f * Mathf.Min(TriArea[t], TriArea[u]) || area <= 1e-9f) return;
                long key = rt < ru ? ((long)rt << 32) | (uint)ru : ((long)ru << 32) | (uint)rt;
                if (!pairs.TryGetValue(key, out var acc))
                {
                    pairs[key] = acc = new Acc { Sample = (A[u] + B[u] + C[u]) / 3f };
                }
                acc.Area += area;
                acc.Tris++;
                if (gap > acc.Gap) acc.Gap = gap;
            }

            int SharedVertices(int t, int u)
            {
                int n = 0;
                if (Same(A[t], A[u]) || Same(A[t], B[u]) || Same(A[t], C[u])) n++;
                if (Same(B[t], A[u]) || Same(B[t], B[u]) || Same(B[t], C[u])) n++;
                if (Same(C[t], A[u]) || Same(C[t], B[u]) || Same(C[t], C[u])) n++;
                return n;
            }

            static bool Same(Vector3 p, Vector3 q) => (p - q).sqrMagnitude < 1e-12f;

            /// <summary>Area of triangle u projected into t's plane and clipped by t (Sutherland-Hodgman).</summary>
            float Overlap(int t, int u)
            {
                var n = N[t];
                var ax = Vector3.Cross(n, Mathf.Abs(n.y) < 0.9f ? Vector3.up : Vector3.right).normalized;
                var ay = Vector3.Cross(n, ax);
                var o = A[t];
                Vector2 P(Vector3 v) { var d = v - o; return new Vector2(Vector3.Dot(d, ax), Vector3.Dot(d, ay)); }
                var c0 = P(A[t]); var c1 = P(B[t]); var c2 = P(C[t]);
                float orient = (c1.x - c0.x) * (c2.y - c0.y) - (c1.y - c0.y) * (c2.x - c0.x);
                float sign = orient >= 0 ? 1f : -1f;
                var src = bufA; var dst = bufB;
                src[0] = P(A[u]); src[1] = P(B[u]); src[2] = P(C[u]);
                int count = 3;
                for (int e = 0; e < 3 && count > 0; e++)
                {
                    var ca = e == 0 ? c0 : e == 1 ? c1 : c2;
                    var cb = e == 0 ? c1 : e == 1 ? c2 : c0;
                    int outCount = 0;
                    for (int i = 0; i < count; i++)
                    {
                        var cur = src[i];
                        var prev = src[(i + count - 1) % count];
                        float sc = ((cb.x - ca.x) * (cur.y - ca.y) - (cb.y - ca.y) * (cur.x - ca.x)) * sign;
                        float sp = ((cb.x - ca.x) * (prev.y - ca.y) - (cb.y - ca.y) * (prev.x - ca.x)) * sign;
                        if (sc >= 0)
                        {
                            if (sp < 0) dst[outCount++] = prev + (cur - prev) * (sp / (sp - sc));
                            dst[outCount++] = cur;
                        }
                        else if (sp >= 0) dst[outCount++] = prev + (cur - prev) * (sp / (sp - sc));
                    }
                    var tmp = src; src = dst; dst = tmp;
                    count = outCount;
                }
                if (count < 3) return 0f;
                float s2 = 0;
                for (int i = 0; i < count; i++)
                {
                    var p = src[i];
                    var q = src[(i + 1) % count];
                    s2 += p.x * q.y - q.x * p.y;
                }
                return Mathf.Abs(s2) * 0.5f;
            }

            string Report(AgentJob job, double seconds, string ending)
            {
                Hits = new List<ZFightPair>();
                foreach (var kv in pairs)
                {
                    if (kv.Value.Area < minArea) continue;
                    var ra = rList[(int)(kv.Key >> 32)];
                    var rb = rList[(int)(kv.Key & 0xffffffff)];
                    Hits.Add(new ZFightPair
                    {
                        A = ra, B = rb,
                        PathA = ra != null ? Util.PathOf(ra.transform) : "<destroyed>",
                        PathB = rb != null ? Util.PathOf(rb.transform) : "<destroyed>",
                        MaterialA = ra != null && ra.sharedMaterial ? ra.sharedMaterial.name : "-",
                        MaterialB = rb != null && rb.sharedMaterial ? rb.sharedMaterial.name : "-",
                        Area = kv.Value.Area, TrianglePairs = kv.Value.Tris, MaxGap = kv.Value.Gap, Sample = kv.Value.Sample,
                    });
                }
                Hits.Sort((x, y) => y.Area.CompareTo(x.Area));

                var sb = new StringBuilder();
                sb.AppendLine(string.Format(Util.Inv,
                    "ZFIGHT scan: scenes={0} root={1} renderers={2} skippedRenderers={3} tris={4} skippedTransparentSubmeshes={5} narrowTests={6} queried={7}",
                    Util.SceneNames(), rootPath ?? "<all>", rList.Count, skippedRenderers, A?.Length ?? lr.Count, skippedTransparent, narrowTests, queried));
                sb.AppendLine(string.Format(Util.Inv,
                    "params: planeEps={0} normalDot={1} minOverlapArea={2} includeSelf={3} includeOppositeFacing={4}",
                    eps, NormalDot, minArea, includeSelf, includeOpp));
                sb.AppendLine(string.Format(Util.Inv, "timing: elapsed={0:0.00}s slices={1} maxSliceMs={2:0.0} workMs={3:0}",
                    seconds, job.Slices, job.MaxSliceMs, job.WorkMs));
                int shown = 0;
                foreach (var h in Hits)
                {
                    if (shown++ >= MaxReport) { sb.AppendLine("... " + (Hits.Count - MaxReport) + " more"); break; }
                    sb.AppendLine(string.Format(Util.Inv, "{0:0.0000} m2  tris={1}  maxGap={2:0.0000}  at {3}{4}\n    A: {5} [{6}]\n    B: {7} [{8}]",
                        h.Area, h.TrianglePairs, h.MaxGap, Util.F3(h.Sample), h.Self ? "  SELF" : "",
                        h.PathA, h.MaterialA, h.PathB, h.MaterialB));
                }
                sb.Append("PAIRS=").Append(Hits.Count.ToString(Util.Inv)).Append(' ').Append(ending);
                return sb.ToString();
            }
        }
    }
}
