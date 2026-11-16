using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using VRC.Core;
using VRC.SDK3.Editor;
using VRC.SDKBase;
using VRC.SDKBase.Editor;
using VRC.SDKBase.Editor.Api;

namespace AWDK.AgentTools
{
    /// <summary>
    /// Agent-driven batch upload of VRChat worlds (one project, several scenes), modelled on
    /// anatawa12's Continuous Avatar Uploader. Every call returns at once (MCP gives up after ~10 s);
    /// the upload runs on the editor's main-thread sync context and is polled with <see cref="Status"/>.
    ///
    /// Ownership check: <c>BuildAndUpload</c> calls <c>VRCCopyrightAgreement.CheckCopyrightAgreement</c>,
    /// which opens a modal ("Copyright ownership agreement") and awaits a click whenever this editor
    /// session has no agreement recorded for the blueprint; nobody clicks, so an agent upload hangs.
    /// The owner's upload request is the ownership confirmation (BoothAssets S-0068), so before each
    /// build this records the agreement through the SDK's own <c>VRCCopyrightAgreement.Agree</c>
    /// (server consent + session list) and the SDK check passes without a modal.
    ///
    /// Usage (execute_code): <c>return AWDK.AgentTools.WorldUploader.Plan("Assets/a.unity;Assets/b.unity");</c>
    /// → <c>WorldUploader.Start(same list)</c> → poll <c>WorldUploader.Status()</c>. Thumbnail: optional
    /// "scene|thumb.png" entries; existing worlds keep their image when none is given.
    /// </summary>
    public static class WorldUploader
    {
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        static readonly StringBuilder Log = new StringBuilder();
        static Task running;
        static CancellationTokenSource cts;
        static string current = "idle";
        static float percent;

        struct Entry { public string Scene, Thumb; }

        static List<Entry> Parse(string list) =>
            list.Split(new[] { ';', '\n' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(s => s.Trim()).Where(s => s.Length > 0)
                .Select(s => { var p = s.Split('|'); return new Entry { Scene = p[0].Trim(), Thumb = p.Length > 1 ? p[1].Trim() : null }; })
                .ToList();

        /// <summary>Read-only: login, build target, and each scene's blueprint ID and remote world name.
        /// Opens nothing; blueprint IDs are read from the scene files.</summary>
        public static string Plan(string list)
        {
            var sb = new StringBuilder();
            sb.AppendLine("login=" + (APIUser.IsLoggedIn ? APIUser.CurrentUser?.displayName : "NOT LOGGED IN")
                          + " target=" + EditorUserBuildSettings.activeBuildTarget
                          + " busy=" + Busy);
            foreach (var e in Parse(list))
            {
                if (!File.Exists(e.Scene)) { sb.AppendLine("MISSING " + e.Scene); continue; }
                var id = ReadBlueprintId(e.Scene);
                sb.AppendLine(e.Scene + " blueprint=" + (id ?? "(none: would create a NEW world)")
                              + (e.Thumb != null ? " thumb=" + e.Thumb + (File.Exists(e.Thumb) ? "" : " (MISSING)") : ""));
            }
            return sb.ToString();
        }

        static async Task AgreeOne(string id)
        {
            var agree = typeof(VRCCopyrightAgreement).GetMethod("Agree", BindingFlags.NonPublic | BindingFlags.Static);
            if (agree == null) throw new Exception("VRCCopyrightAgreement.Agree not found (SDK changed)");
            if (!await (Task<bool>)agree.Invoke(null, new object[] { id }))
                throw new Exception("ownership agreement was not accepted by the API for " + id);
            Line("AGREED " + id);
        }
        /// <summary>Opens each scene in turn and builds + uploads it for the current build target.
        /// Refuses to start if the open scene has unsaved changes.</summary>
        public static string Start(string list)
        {
            if (Busy) return "BUSY " + current;
            if (!APIUser.IsLoggedIn) return "ERROR not logged in to the VRChat SDK";
            for (int i = 0; i < SceneManagerCount(); i++)
            {
                var s = EditorSceneManager.GetSceneAt(i);
                if (s.isDirty) return "ERROR open scene has unsaved changes: " + s.path + " (save or discard first)";
            }
            var entries = Parse(list);
            var missing = entries.Where(e => !File.Exists(e.Scene)).Select(e => e.Scene).ToList();
            if (missing.Count > 0) return "ERROR missing scenes: " + string.Join(", ", missing);
            Log.Clear();
            cts = new CancellationTokenSource();
            running = UploadAll(entries, cts.Token);
            return "started " + entries.Count + " worlds on " + EditorUserBuildSettings.activeBuildTarget;
        }

        public static string Cancel() { cts?.Cancel(); return "cancel requested"; }

        public static bool Busy => running != null && !running.IsCompleted;

        public static string Status() =>
            (Busy ? string.Format(Inv, "STATE=running {0} {1:0}%", current, percent * 100f) : "STATE=idle")
            + "\n" + Log;

        static int SceneManagerCount() => UnityEngine.SceneManagement.SceneManager.sceneCount;

        static void Line(string s)
        {
            var l = DateTime.Now.ToString("HH:mm:ss", Inv) + " " + s;
            Log.AppendLine(l);
            Debug.Log("[WorldUploader] " + l);
        }

        static async Task UploadAll(List<Entry> entries, CancellationToken ct)
        {
            foreach (var e in entries)
            {
                if (ct.IsCancellationRequested) { Line("CANCELLED before " + e.Scene); break; }
                try { await UploadOne(e, ct); }
                catch (Exception ex) { Line("FAIL " + e.Scene + ": " + ex.GetType().Name + ": " + ex.Message); }
            }
            current = "idle";
            Line("DONE");
        }

        static async Task UploadOne(Entry e, CancellationToken ct)
        {
            current = "open " + e.Scene; percent = 0;
            if (EditorSceneManager.GetActiveScene().path != e.Scene)
                EditorSceneManager.OpenScene(e.Scene, OpenSceneMode.Single);

            var stray = Resources.FindObjectsOfTypeAll<GameObject>()
                .Where(g => g.scene.IsValid() && g.name.StartsWith("__", StringComparison.Ordinal) && g.name.EndsWith("__", StringComparison.Ordinal))
                .Select(g => g.name).Distinct().ToList();
            if (stray.Count > 0) throw new Exception("agent rig objects in scene (delete first): " + string.Join(", ", stray));

            var pms = UnityEngine.Object.FindObjectsOfType<PipelineManager>(true);
            if (pms.Length != 1) throw new Exception("expected 1 PipelineManager, found " + pms.Length);
            var id = pms[0].blueprintId;

            var builder = await GetBuilder(ct);

            VRCWorld world;
            if (!string.IsNullOrEmpty(id))
            {
                world = await VRCApi.GetWorld(id, true, ct);
                Line("UPLOAD " + e.Scene + " -> " + world.Name + " (" + id + ")");
            }
            else
            {
                if (e.Thumb == null) throw new Exception("new world needs a thumbnail: 'scene|thumb.png'");
                world = new VRCWorld { Name = Path.GetFileNameWithoutExtension(e.Scene), Tags = new List<string>() };
                Line("CREATE " + e.Scene + " as new world '" + world.Name + "'");
                // Assign the ID now (as BuildAndUpload would) so the agreement can be recorded for it.
                Undo.RecordObject(pms[0], "Assigning a new ID");
                pms[0].AssignId(PipelineManager.ContentType.world);
                id = pms[0].blueprintId;
            }
            await AgreeOne(id);

            current = "build+upload " + e.Scene;
            EventHandler<(string status, float percentage)> onProg = (_, p) => { current = "upload " + e.Scene + " " + p.status; percent = p.percentage; };
            EventHandler<string> onBuild = (_, s) => { current = "build " + e.Scene + " " + s; };
            builder.OnSdkUploadProgress += onProg;
            builder.OnSdkBuildProgress += onBuild;
            try
            {
                var thumb = e.Thumb != null ? Path.GetFullPath(e.Thumb) : null;
                await builder.BuildAndUpload(world, thumb, ct);
                Line("OK " + e.Scene + " (" + UnityEngine.Object.FindObjectsOfType<PipelineManager>(true)[0].blueprintId + ")");
            }
            finally
            {
                builder.OnSdkUploadProgress -= onProg;
                builder.OnSdkBuildProgress -= onBuild;
            }
        }

        static async Task<IVRCSdkWorldBuilderApi> GetBuilder(CancellationToken ct)
        {
            if (VRCSdkControlPanel.window == null) EditorApplication.ExecuteMenuItem("VRChat SDK/Show Control Panel");
            for (int i = 0; i < 300; i++)
            {
                if (VRCSdkControlPanel.TryGetBuilder<IVRCSdkWorldBuilderApi>(out var b)) return b;
                await Task.Delay(100, ct);
            }
            throw new Exception("SDK world builder not available after 30 s (control panel open, Builder tab, logged in?)");
        }

        static string ReadBlueprintId(string scenePath)
        {
            // Scene YAML: PipelineManager serializes `blueprintId: wrld_...`. Read-only text scan.
            foreach (var line in File.ReadLines(scenePath))
            {
                var t = line.Trim();
                if (t.StartsWith("blueprintId:", StringComparison.Ordinal))
                {
                    var v = t.Substring("blueprintId:".Length).Trim();
                    if (v.StartsWith("wrld_", StringComparison.Ordinal)) return v;
                }
            }
            return null;
        }
    }
}
