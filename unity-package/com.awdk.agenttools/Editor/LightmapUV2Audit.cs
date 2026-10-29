using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace AWDK.AgentTools
{
    /// <summary>
    /// Read-only lightmap UV2 audit (skill lightmap-allocation, references/audit.md). One TSV row per MeshRenderer under a root.
    /// Run(root, tsv) is synchronous (use it for one room or a few hundred renderers); Start/Status is the time-sliced job
    /// for a whole scene (a 40 ms budget per editor tick, so the editor stays responsive).
    /// Texel numbers use the baked scale/offset and atlas size when the renderer is lightmapped (T = atlasSize * sqrt(|so.x*so.y|)),
    /// else an estimate from Scale In Lightmap at <see cref="FallbackTexelsPerMeter"/>. A negative scale/offset still counts as baked
    /// (Bakery writes one when a chart rect is narrower than twice its padding, so the chart is tiny and mirrored): it uses |so| and
    /// is flagged NEG_SO in the negSO column.
    /// All numbers are written with InvariantCulture.
    /// </summary>
    public static class LightmapUV2Audit
    {
        public static float FallbackTexelsPerMeter = 20f;   // Lighting "Lightmap Resolution" when the renderer is not baked
        public static float GutterPadding = 2f;              // texels of chart padding the bake used
        const string Header = "path\tmesh\tmaterials\tmode\tgroup\tboundsSmall\tboundsMiddle\tboundsLarge\tworldArea\tuv2Area\tT\ttexelsPerM\ttinyTriFrac\tcharts\ttinyChartFrac\tchartsPerTri\tworstSubmesh\tworstUv2Share\tworstAreaShare\tshare\tshortSideTexels\tminGapTexels\tuv2Valid\ttransparent\ttris\tnegSO\tflags";
        static readonly CultureInfo CI = CultureInfo.InvariantCulture;

        // ------------------------------------------------------------------ job state
        static List<MeshRenderer> jobList; static int jobIdx; static StringBuilder jobRows; static string jobOut; static string jobRoot;
        static Dictionary<string, int> jobCounts; static List<Row> jobRowsData; static string jobStatus = "idle";

        class Row { public string path, mode; public int lmi; public float share; public string flags = ""; public StringBuilder line; }

        /// <summary>Synchronous audit of every MeshRenderer under rootPath ("" = whole scene). Returns the flag counts.</summary>
        public static string Run(string rootPath, string outTsv)
        {
            var list = Collect(rootPath);
            var rows = new List<Row>(); var sb = new StringBuilder(Header + "\n");
            foreach (var r in list) rows.Add(AuditOne(r));
            return Finish(rows, sb, outTsv, rootPath);
        }

        /// <summary>Starts the time-sliced job. Poll Status() until it starts with "DONE".</summary>
        public static string Start(string rootPath, string outTsv)
        {
            if (jobStatus.StartsWith("RUNNING")) return "already running: " + jobStatus;
            jobList = Collect(rootPath); jobIdx = 0; jobRowsData = new List<Row>(); jobOut = outTsv; jobRoot = rootPath;
            jobStatus = "RUNNING 0/" + jobList.Count;
            EditorApplication.update += Tick;
            return jobStatus;
        }

        public static string Status() => jobStatus;

        static void Tick()
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            while (jobIdx < jobList.Count && sw.ElapsedMilliseconds < 40)
            {
                var r = jobList[jobIdx++];
                if (r != null) jobRowsData.Add(AuditOne(r));
            }
            jobStatus = "RUNNING " + jobIdx + "/" + jobList.Count;
            if (jobIdx < jobList.Count) return;
            EditorApplication.update -= Tick;
            jobStatus = "DONE " + Finish(jobRowsData, new StringBuilder(Header + "\n"), jobOut, jobRoot);
        }

        static List<MeshRenderer> Collect(string rootPath)
        {
            var list = new List<MeshRenderer>();
            IEnumerable<MeshRenderer> src;
            if (string.IsNullOrEmpty(rootPath)) src = UnityEngine.Object.FindObjectsOfType<MeshRenderer>(true);
            else
            {
                var root = GameObject.Find(rootPath);
                if (root == null) throw new ArgumentException("root not found: " + rootPath);
                src = root.GetComponentsInChildren<MeshRenderer>(true);
            }
            foreach (var r in src)
            {
                var mf = r.GetComponent<MeshFilter>();
                if (mf == null || mf.sharedMesh == null) continue;
                list.Add(r);
            }
            return list;
        }

        // ------------------------------------------------------------------ per renderer
        static Row AuditOne(MeshRenderer r)
        {
            var row = new Row { path = PathOf(r.transform), lmi = r.lightmapIndex };
            var mesh = r.GetComponent<MeshFilter>().sharedMesh;
            var flags = new List<string>();
            var uv = mesh.uv2; var vs = mesh.vertices;
            var statics = GameObjectUtility.GetStaticEditorFlags(r.gameObject);
            bool contrib = (statics & StaticEditorFlags.ContributeGI) != 0;
            string mode = !contrib ? "D" : (r.receiveGI == ReceiveGI.LightProbes ? "P" : "L"); row.mode = mode;
            var group = GroupName(r);
            var mats = new List<string>(); bool transparent = false;
            foreach (var m in r.sharedMaterials)
            {
                if (m == null) { mats.Add("null"); continue; }
                mats.Add(m.name);
                string ln = m.name.ToLowerInvariant();
                if (m.renderQueue >= 2500 || ln.Contains("glass") || ln.Contains("window") || ln.Contains("glazing")
                    || (m.HasProperty("_Mode") && m.GetFloat("_Mode") >= 2f)) transparent = true;
            }
            var bs = r.bounds.size; var dims = new[] { bs.x, bs.y, bs.z }; Array.Sort(dims);
            var so = r.lightmapScaleOffset;
            bool baked = r.lightmapIndex >= 0 && r.lightmapIndex < 65534;
            bool finite = IsFinite(so.x) && IsFinite(so.y) && IsFinite(so.z) && IsFinite(so.w);
            bool negSO = baked && finite && (so.x < 0f || so.y < 0f);
            bool uvValid = uv != null && uv.Length == vs.Length && uv.Length > 0;
            if (uvValid) foreach (var u in uv) if (!IsFinite(u.x) || !IsFinite(u.y) || u.x < -0.0001f || u.y < -0.0001f || u.x > 1.0001f || u.y > 1.0001f) { uvValid = false; break; }

            double worldArea = 0, uv2Area = 0, T = 0, tpm = 0, tinyTriFrac = 0, tinyChartFrac = 0, chartsPerTri = 0, short_ = 0, minGap = -1, share = 0;
            int charts = 0, nt = 0; string worstSub = "-"; double worstU = 0, worstA = 0;
            if (uv != null && uv.Length == vs.Length && uv.Length > 0)
            {
                var m = r.transform.localToWorldMatrix; var wv = new Vector3[vs.Length];
                for (int i = 0; i < vs.Length; i++) wv[i] = m.MultiplyPoint3x4(vs[i]);
                // weld UV2 positions into ids, union-find over triangles: a chart = connected component by shared UV2 vertex
                var keyId = new Dictionary<long, int>(); var vid = new int[vs.Length];
                for (int i = 0; i < vs.Length; i++)
                {
                    long key = ((long)Mathf.RoundToInt(uv[i].x * 100000f) << 32) ^ (uint)Mathf.RoundToInt(uv[i].y * 100000f);
                    if (!keyId.TryGetValue(key, out int id)) { id = keyId.Count; keyId[key] = id; }
                    vid[i] = id;
                }
                var par = new int[keyId.Count]; for (int i = 0; i < par.Length; i++) par[i] = i;
                Func<int, int> find = null; find = a => { while (par[a] != a) { par[a] = par[par[a]]; a = par[a]; } return a; };
                int subCount = mesh.subMeshCount; var subW = new double[subCount]; var subU = new double[subCount];
                var triWorld = new List<double>(); var triUv = new List<double>(); var triChart = new List<int>(); var triSub = new List<int>();
                var tris = new List<int>();
                for (int s = 0; s < subCount; s++)
                {
                    var ts = mesh.GetTriangles(s);
                    for (int t = 0; t < ts.Length; t += 3)
                    {
                        int a = ts[t], b = ts[t + 1], c = ts[t + 2];
                        tris.Add(a); tris.Add(b); tris.Add(c); triSub.Add(s);
                        int ra = find(vid[a]), rb = find(vid[b]), rc = find(vid[c]); par[rb] = ra; par[rc] = ra;
                        double wa = Vector3.Cross(wv[b] - wv[a], wv[c] - wv[a]).magnitude * 0.5;
                        Vector2 pa = uv[a], pb = uv[b], pc = uv[c];
                        double ua = Math.Abs((pb.x - pa.x) * (pc.y - pa.y) - (pc.x - pa.x) * (pb.y - pa.y)) * 0.5;
                        triWorld.Add(wa); triUv.Add(ua); worldArea += wa; uv2Area += ua; subW[s] += wa; subU[s] += ua;
                    }
                }
                nt = triWorld.Count;
                for (int t = 0; t < nt; t++) triChart.Add(find(vid[tris[3 * t]]));
                // T: texels per UV unit
                if (baked && finite && so.x != 0f && so.y != 0f)
                {
                    int atlas = AtlasSize(r.lightmapIndex);
                    T = atlas * Math.Sqrt(Math.Abs(so.x * so.y));
                }
                else
                {
                    float scale = ScaleInLightmap(r);
                    T = FallbackTexelsPerMeter * scale * (uv2Area > 1e-12 ? Math.Sqrt(worldArea / uv2Area) : 0);
                }
                tpm = (worldArea > 1e-12 && uv2Area > 1e-12) ? T * Math.Sqrt(uv2Area / worldArea) : 0;
                int tinyTris = 0; var chartArea = new Dictionary<int, double>(); var cmin = new Dictionary<int, Vector2>(); var cmax = new Dictionary<int, Vector2>();
                for (int t = 0; t < nt; t++)
                {
                    if (triUv[t] * T * T < 0.01) tinyTris++;
                    int ch = triChart[t];
                    if (!chartArea.ContainsKey(ch)) { chartArea[ch] = 0; cmin[ch] = new Vector2(9, 9); cmax[ch] = new Vector2(-9, -9); }
                    chartArea[ch] += triUv[t];
                    for (int k = 0; k < 3; k++) { var p = uv[tris[3 * t + k]]; cmin[ch] = Vector2.Min(cmin[ch], p); cmax[ch] = Vector2.Max(cmax[ch], p); }
                }
                charts = chartArea.Count; int tinyCharts = 0;
                foreach (var kv in chartArea) if (Math.Sqrt(kv.Value) * T < 4.0) tinyCharts++;
                tinyTriFrac = nt > 0 ? (double)tinyTris / nt : 0; tinyChartFrac = charts > 0 ? (double)tinyCharts / charts : 0; chartsPerTri = nt > 0 ? (double)charts / nt : 0;
                short_ = tpm * dims[1];
                // worst submesh: lowest uv2Share / areaShare among submeshes with a meaningful area share
                double worstRatio = double.MaxValue;
                for (int s = 0; s < subCount; s++)
                {
                    if (worldArea <= 1e-12 || uv2Area <= 1e-12) break;
                    double aS = subW[s] / worldArea, uS = subU[s] / uv2Area;
                    if (aS < 0.02) continue;
                    double ratio = uS / aS;
                    if (ratio < worstRatio) { worstRatio = ratio; worstSub = s.ToString(CI); worstU = uS; worstA = aS; }
                }
                // min gap between chart bounding boxes (large meshes only, sampled)
                if (dims[2] >= 1.3f && charts > 1 && charts <= 4000)
                {
                    var keys = new List<int>(chartArea.Keys); int n = keys.Count; int stride = Math.Max(1, n / 200); double best = double.MaxValue;
                    for (int i = 0; i < n; i += stride)
                        for (int j = i + 1; j < n; j += stride)
                        {
                            var a0 = cmin[keys[i]]; var a1 = cmax[keys[i]]; var b0 = cmin[keys[j]]; var b1 = cmax[keys[j]];
                            double gx = Math.Max(0, Math.Max(b0.x - a1.x, a0.x - b1.x)); double gy = Math.Max(0, Math.Max(b0.y - a1.y, a0.y - b1.y));
                            if (gx > 0 && gy > 0) continue; // diagonal neighbours do not touch
                            double g = Math.Max(gx, gy); if (g < best) best = g;
                        }
                    if (best < double.MaxValue) minGap = best * T;
                }
            }
            share = baked && finite ? Math.Abs(so.x * so.y) : 0;

            // ------------------------------------------------------------ flags
            bool lit = mode == "L";
            if (!uvValid && mode != "D") flags.Add("UV2_INVALID");
            if (negSO) flags.Add("NEG_SO");
            if (!finite) flags.Add("NONFINITE_SO");
            if (lit && nt > 0 && tinyTriFrac > 0.30) flags.Add("FRAG_TRIS");
            if (lit && charts > 0 && tinyChartFrac > 0.50) flags.Add("FRAG_CHARTS");
            if (lit && worstSub != "-" && worstA >= 0.10 && worstU < 0.05) flags.Add("SUBMESH_STARVED");
            if (nt > 0 && chartsPerTri >= 0.9) flags.Add("DUP_TRIS");
            if (lit && transparent) flags.Add("TRANSPARENT_L");
            if (lit && (dims[2] < 0.12f || (dims[1] < 0.12f && short_ < 12))) flags.Add("TOO_SMALL");
            if (lit && baked && short_ > 0 && short_ < 8) flags.Add("SHORT_SIDE");
            if (lit && minGap >= 0 && minGap < GutterPadding + 1) flags.Add("GUTTER");
            if (lit && baked && finite && so.x == 1f && so.y == 1f && so.z == 0f && so.w == 0f) flags.Add("UNGROUPED");
            if (mode == "P" && group != "none") flags.Add("SELECTOR_ON_P");
            var lg = r.GetComponentInParent<LODGroup>();
            if (lg != null && lg.enabled && r.GetComponentInParent<LODGroup>() != null && lg.GetLODs().Length > 1)
            {
                // a renderer in a LODGroup must be baked per LOD level; flag when a lit renderer sits in a multi-level group
                if (lit) flags.Add("LOD_GROUP");
            }
            if (lit && (r.GetComponent<UnityEngine.Video.VideoPlayer>() != null || (r.sharedMaterial != null && r.sharedMaterial.name.ToLowerInvariant().Contains("mirror")))) flags.Add("GI_SCREEN");
            row.flags = string.Join(",", flags); row.share = (float)share;

            var line = new StringBuilder();
            Action<object> add = o => { line.Append(o is double d ? d.ToString("0.####", CI) : (o is float f ? f.ToString("0.####", CI) : Convert.ToString(o, CI))); line.Append('\t'); };
            add(row.path); add(mesh.name); add(string.Join("|", mats)); add(mode); add(group);
            add(dims[0]); add(dims[1]); add(dims[2]); add(worldArea); add(uv2Area); add(T); add(tpm); add(tinyTriFrac); add(charts); add(tinyChartFrac); add(chartsPerTri);
            add(worstSub); add(worstU); add(worstA); add(share); add(short_); add(minGap); add(uvValid ? 1 : 0); add(transparent ? 1 : 0); add(nt); add(negSO ? 1 : 0);
            line.Append(row.flags);
            row.line = line;
            return row;
        }

        // ------------------------------------------------------------------ output
        static string Finish(List<Row> rows, StringBuilder sb, string outTsv, string rootPath)
        {
            // HOG: top 10 by share per atlas, share > 0.10
            var perAtlas = new Dictionary<int, List<Row>>();
            foreach (var r in rows) if (r.mode == "L" && r.lmi >= 0 && r.lmi < 65534) { if (!perAtlas.TryGetValue(r.lmi, out var l)) perAtlas[r.lmi] = l = new List<Row>(); l.Add(r); }
            foreach (var kv in perAtlas) { kv.Value.Sort((a, b) => b.share.CompareTo(a.share)); for (int i = 0; i < Math.Min(10, kv.Value.Count); i++) if (kv.Value[i].share > 0.10f) kv.Value[i].flags = kv.Value[i].flags.Length == 0 ? "HOG" : kv.Value[i].flags + ",HOG"; }
            var counts = new SortedDictionary<string, int>();
            foreach (var r in rows)
            {
                if (r.line == null) continue;
                // rebuild the flags column (HOG may have been appended after the line was built)
                string s = r.line.ToString(); int cut = s.LastIndexOf('\t'); s = s.Substring(0, cut + 1) + r.flags;
                sb.Append(s).Append('\n');
                if (r.flags.Length > 0) foreach (var f in r.flags.Split(',')) { counts.TryGetValue(f, out int c); counts[f] = c + 1; }
            }
            if (!string.IsNullOrEmpty(outTsv)) { Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outTsv))); File.WriteAllText(outTsv, sb.ToString()); }
            var res = new StringBuilder("renderers=" + rows.Count + " root=" + (string.IsNullOrEmpty(rootPath) ? "<scene>" : rootPath));
            foreach (var kv in counts) res.Append(' ').Append(kv.Key).Append('=').Append(kv.Value);
            return res.ToString();
        }

        // ------------------------------------------------------------------ helpers
        static bool IsFinite(float f) => !float.IsNaN(f) && !float.IsInfinity(f);

        static int AtlasSize(int index)
        {
            var lms = LightmapSettings.lightmaps;
            if (index >= 0 && index < lms.Length && lms[index].lightmapColor != null) return lms[index].lightmapColor.width;
            return 1024;
        }

        static float ScaleInLightmap(MeshRenderer r)
        {
            var so = new SerializedObject(r); var p = so.FindProperty("m_ScaleInLightmap");
            return p != null ? p.floatValue : 1f;
        }

        static string GroupName(Component c)
        {
            for (var t = c.transform; t != null; t = t.parent)
                foreach (var comp in t.GetComponents<MonoBehaviour>())
                {
                    if (comp == null || comp.GetType().Name != "BakeryLightmapGroupSelector") continue;
                    var f = comp.GetType().GetField("lmgroupAsset");
                    var asset = f != null ? f.GetValue(comp) as UnityEngine.Object : null;
                    return asset != null ? asset.name : "none";
                }
            return "none";
        }

        static string PathOf(Transform t)
        {
            var sb = new StringBuilder(t.name);
            for (var p = t.parent; p != null; p = p.parent) sb.Insert(0, p.name + "/");
            return sb.ToString();
        }
    }
}
