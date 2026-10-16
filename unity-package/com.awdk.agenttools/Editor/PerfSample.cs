using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using Unity.Profiling;
using UnityEditor;
using UnityEngine;

namespace AWDK.AgentTools
{
    /// <summary>
    /// Play-mode performance sample. Waits settleSeconds (real time), optionally disables every
    /// renderer under the listed roots (play-mode change: reverted when play mode exits, and restored
    /// at the end of the sample), skips warmupFrames, then records frames: CPU frame time, main thread,
    /// Camera.Render and BehaviourUpdate profiler markers, GPU frame time (FrameTimingManager; null when
    /// the platform/editor does not provide it), draw calls / batches / set-pass calls / triangles /
    /// vertices (UnityEditor.UnityStats, via reflection). Writes a JSON file and returns a summary.
    /// Editor numbers include editor overhead and every camera that renders (Game view, and Scene view
    /// when visible): compare runs against each other, not against a VRChat client.
    /// </summary>
    public static class PerfSample
    {
        public const string Kind = "PerfSample";

        public static string Start(string outJson, float settleSeconds = 15, int warmupFrames = 40, int frames = 200, string disableRootsCsv = null)
        {
            if (!EditorApplication.isPlaying) return "ERROR PerfSample needs play mode: enter play mode first, then call Start again";
            if (frames < 1) return "ERROR frames must be >= 1";
            if (string.IsNullOrWhiteSpace(outJson)) return "ERROR outJson is empty";
            string path = Path.GetFullPath(Path.IsPathRooted(outJson) ? outJson : Path.Combine(Directory.GetCurrentDirectory(), outJson));
            var roots = new List<string>();
            if (!string.IsNullOrWhiteSpace(disableRootsCsv))
                foreach (var part in disableRootsCsv.Split(','))
                    if (part.Trim().Length > 0) roots.Add(part.Trim());
            var missing = roots.FindAll(r => Util.ResolveRoots(r).Count == 0);
            if (missing.Count > 0) return "ERROR roots not found: " + string.Join(", ", missing);
            JobRunner.Start(Kind, job => Run(job, path, Mathf.Max(0, settleSeconds), Mathf.Max(0, warmupFrames), frames, roots));
            return string.Format(Util.Inv, "STARTED PerfSample settle={0}s warmup={1} frames={2} disable=[{3}] out={4}; poll PerfSample.Status()",
                settleSeconds, warmupFrames, frames, string.Join(",", roots), path);
        }

        public static string Status() => JobRunner.Status(Kind);

        static readonly string[] StatNames = { "drawCalls", "batches", "setPassCalls", "triangles", "vertices" };

        static IEnumerator Run(AgentJob job, string path, float settle, int warmup, int frames, List<string> roots)
        {
            double settleEnd = EditorApplication.timeSinceStartup + settle;
            while (EditorApplication.timeSinceStartup < settleEnd)
            {
                if (!EditorApplication.isPlaying) { job.Result = "ERROR play mode ended during settle"; yield break; }
                job.Progress = string.Format(Util.Inv, "settle {0:0.0}s left", settleEnd - EditorApplication.timeSinceStartup);
                yield return JobRunner.EndSlice;
            }

            var disabled = new List<Renderer>();
            foreach (var root in roots)
                foreach (var t in Util.ResolveRoots(root))
                    foreach (var r in t.GetComponentsInChildren<Renderer>(true))
                        if (r.enabled) { r.enabled = false; disabled.Add(r); }

            var statProps = new PropertyInfo[StatNames.Length];
            var statsType = typeof(Editor).Assembly.GetType("UnityEditor.UnityStats");
            for (int i = 0; i < StatNames.Length; i++)
                statProps[i] = statsType?.GetProperty(StatNames[i], BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);

            var cpu = new List<double>(); var main = new List<double>(); var camR = new List<double>(); var beh = new List<double>(); var gpu = new List<double>();
            var stats = new List<double>[StatNames.Length];
            for (int i = 0; i < stats.Length; i++) stats[i] = new List<double>();
            var recMain = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread");
            var recCam = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Camera.Render");
            var recBeh = ProfilerRecorder.StartNew(ProfilerCategory.Scripts, "BehaviourUpdate");
            var timings = new FrameTiming[1];
            try
            {
                int startFrame = Time.frameCount;
                int lastFrame = startFrame;
                while (Time.frameCount - startFrame < warmup)
                {
                    if (!EditorApplication.isPlaying) { job.Result = "ERROR play mode ended during warmup"; yield break; }
                    job.Progress = string.Format(Util.Inv, "warmup {0}/{1}", Time.frameCount - startFrame, warmup);
                    yield return JobRunner.EndSlice;
                }
                lastFrame = Time.frameCount;
                while (cpu.Count < frames)
                {
                    if (!EditorApplication.isPlaying) { job.Result = "ERROR play mode ended during sampling"; yield break; }
                    if (Time.frameCount != lastFrame)
                    {
                        lastFrame = Time.frameCount;
                        cpu.Add(Time.unscaledDeltaTime * 1000.0);
                        if (recMain.Valid) main.Add(recMain.LastValue / 1e6);
                        if (recCam.Valid) camR.Add(recCam.LastValue / 1e6);
                        if (recBeh.Valid) beh.Add(recBeh.LastValue / 1e6);
                        FrameTimingManager.CaptureFrameTimings();
                        if (FrameTimingManager.GetLatestTimings(1, timings) > 0 && timings[0].gpuFrameTime > 0) gpu.Add(timings[0].gpuFrameTime);
                        for (int i = 0; i < StatNames.Length; i++)
                            if (statProps[i] != null) stats[i].Add(Convert.ToDouble(statProps[i].GetValue(null), Util.Inv));
                        job.Progress = string.Format(Util.Inv, "sample {0}/{1}", cpu.Count, frames);
                    }
                    yield return JobRunner.EndSlice;
                }
            }
            finally
            {
                recMain.Dispose(); recCam.Dispose(); recBeh.Dispose();
                foreach (var r in disabled) if (r != null) r.enabled = true;
            }

            var sb = new StringBuilder();
            sb.Append("{\n");
            sb.AppendFormat(Util.Inv, "  \"scenes\": {0},\n", Json(Util.SceneNames()));
            sb.AppendFormat(Util.Inv, "  \"unityVersion\": {0},\n", Json(Application.unityVersion));
            sb.AppendFormat(Util.Inv, "  \"timestampUtc\": {0},\n", Json(DateTime.UtcNow.ToString("o", Util.Inv)));
            sb.AppendFormat(Util.Inv, "  \"settleSeconds\": {0},\n  \"warmupFrames\": {1},\n  \"frames\": {2},\n", settle, warmup, cpu.Count);
            sb.AppendFormat(Util.Inv, "  \"disabledRoots\": [{0}],\n  \"disabledRenderers\": {1},\n", string.Join(", ", roots.ConvertAll(Json)), disabled.Count);
            sb.AppendFormat(Util.Inv, "  \"cpuFrameMs\": {0},\n", StatsJson(cpu));
            sb.AppendFormat(Util.Inv, "  \"mainThreadMs\": {0},\n", StatsJson(main));
            sb.AppendFormat(Util.Inv, "  \"cameraRenderMs\": {0},\n", StatsJson(camR));
            sb.AppendFormat(Util.Inv, "  \"behaviourUpdateMs\": {0},\n", StatsJson(beh));
            sb.AppendFormat(Util.Inv, "  \"gpuFrameMs\": {0},\n", StatsJson(gpu));
            for (int i = 0; i < StatNames.Length; i++)
                sb.AppendFormat(Util.Inv, "  \"{0}\": {1},\n", StatNames[i], StatsJson(stats[i]));
            sb.Append("  \"notes\": \"Editor play-mode numbers: include editor overhead and every rendering camera. Compare runs with each other. gpuFrameMs is null when FrameTimingManager has no data (enable Frame Timing Stats in Player settings).\"\n");
            sb.Append("}\n");
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, sb.ToString());

            job.Result = string.Format(Util.Inv,
                "PERF frames={0} disabledRenderers={1}\ncpuFrameMs median={2:0.00} p95={3:0.00}\ncameraRenderMs median={4:0.00}\nbehaviourUpdateMs median={5:0.00}\ngpuFrameMs median={6}\ndrawCalls median={7:0} batches median={8:0} triangles median={9:0}\nJSON={10}\nCOMPLETE",
                cpu.Count, disabled.Count, Med(cpu), P95(cpu), Med(camR), Med(beh),
                gpu.Count > 0 ? Med(gpu).ToString("0.00", Util.Inv) : "n/a", Med(stats[0]), Med(stats[1]), Med(stats[3]), path);
        }

        static double Med(List<double> v) { if (v.Count == 0) return double.NaN; var s = new List<double>(v); s.Sort(); return Util.Percentile(s, 0.5); }
        static double P95(List<double> v) { if (v.Count == 0) return double.NaN; var s = new List<double>(v); s.Sort(); return Util.Percentile(s, 0.95); }

        static string StatsJson(List<double> v)
        {
            if (v.Count == 0) return "null";
            var s = new List<double>(v);
            s.Sort();
            double sum = 0;
            foreach (var x in s) sum += x;
            return string.Format(Util.Inv, "{{\"mean\": {0:0.###}, \"median\": {1:0.###}, \"p95\": {2:0.###}, \"min\": {3:0.###}, \"max\": {4:0.###}, \"n\": {5}}}",
                sum / s.Count, Util.Percentile(s, 0.5), Util.Percentile(s, 0.95), s[0], s[s.Count - 1], s.Count);
        }

        static string Json(string s)
        {
            var sb = new StringBuilder("\"");
            foreach (var c in s ?? "")
            {
                if (c == '"' || c == '\\') sb.Append('\\').Append(c);
                else if (c < ' ') sb.AppendFormat(Util.Inv, "\\u{0:x4}", (int)c);
                else sb.Append(c);
            }
            return sb.Append('"').ToString();
        }
    }
}
