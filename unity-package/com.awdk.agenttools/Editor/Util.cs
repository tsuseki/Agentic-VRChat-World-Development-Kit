using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace AWDK.AgentTools
{
    /// <summary>One camera shot, parsed from the shots JSON shared by WorldCapture and ZFightRender.</summary>
    [Serializable]
    public sealed class Shot
    {
        public string name;
        public float[] pos;
        public float[] look;
        public float fov;
        public int w;
        public int h;
        /// <summary>Optional near clip plane (default 0.03).</summary>
        public float near;
        /// <summary>Optional far clip plane (default 1000).</summary>
        public float far;

        public Vector3 Pos => Util.Vec(pos, "pos");
        public Vector3 Look => Util.Vec(look, "look");
    }

    public static class Util
    {
        public static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        public const string CapCamName = "__CapCam__";

        public static string F3(Vector3 v) => string.Format(Inv, "({0:0.###}, {1:0.###}, {2:0.###})", v.x, v.y, v.z);

        public static string PathOf(Transform t)
        {
            if (t == null) return "<destroyed>";
            var s = t.name;
            while (t.parent != null) { t = t.parent; s = t.name + "/" + s; }
            return s;
        }

        internal static Vector3 Vec(float[] a, string what)
        {
            if (a == null || a.Length != 3) throw new ArgumentException("shot." + what + " must be [x,y,z]");
            return new Vector3(a[0], a[1], a[2]);
        }

        /// <summary>
        /// Resolves "Root/Child/Grandchild" across every loaded scene (inactive objects included).
        /// Null or empty means every root object of every loaded scene. Returns an empty list when
        /// nothing matches.
        /// </summary>
        public static List<Transform> ResolveRoots(string rootPath)
        {
            var result = new List<Transform>();
            string path = string.IsNullOrEmpty(rootPath) ? null : rootPath.Trim().Trim('/');
            for (int s = 0; s < SceneManager.sceneCount; s++)
            {
                var scene = SceneManager.GetSceneAt(s);
                if (!scene.isLoaded) continue;
                foreach (var go in scene.GetRootGameObjects())
                {
                    if (path == null) { result.Add(go.transform); continue; }
                    int slash = path.IndexOf('/');
                    string first = slash < 0 ? path : path.Substring(0, slash);
                    if (go.name != first) continue;
                    var t = slash < 0 ? go.transform : go.transform.Find(path.Substring(slash + 1));
                    if (t != null) result.Add(t);
                }
            }
            return result;
        }

        public static string SceneNames()
        {
            var names = new List<string>();
            for (int s = 0; s < SceneManager.sceneCount; s++)
            {
                var sc = SceneManager.GetSceneAt(s);
                if (sc.isLoaded) names.Add(string.IsNullOrEmpty(sc.path) ? "<unsaved:" + sc.name + ">" : sc.path);
            }
            return string.Join(",", names);
        }

        /// <summary>True when the object or an ancestor is tagged EditorOnly (stripped from uploads).</summary>
        public static bool IsEditorOnly(Transform t)
        {
            for (; t != null; t = t.parent)
                if (t.CompareTag("EditorOnly")) return true;
            return false;
        }

        /// <summary>True when the type or one of its base types has one of the given simple names.</summary>
        public static bool TypeNamed(Type type, params string[] names)
        {
            for (var t = type; t != null && t != typeof(MonoBehaviour); t = t.BaseType)
                foreach (var n in names)
                    if (t.Name == n) return true;
            return false;
        }

        public static Shot[] ParseShots(string shotsJson)
        {
            if (string.IsNullOrWhiteSpace(shotsJson)) throw new ArgumentException("shotsJson is empty");
            var trimmed = shotsJson.Trim();
            if (!trimmed.StartsWith("[")) trimmed = "[" + trimmed + "]";
            var wrap = JsonUtility.FromJson<ShotList>("{\"shots\":" + trimmed + "}");
            if (wrap?.shots == null || wrap.shots.Length == 0) throw new ArgumentException("shotsJson has no shots");
            for (int i = 0; i < wrap.shots.Length; i++)
            {
                var s = wrap.shots[i];
                if (string.IsNullOrEmpty(s.name)) s.name = (i + 1).ToString("00", Inv);
                foreach (var c in Path.GetInvalidFileNameChars()) s.name = s.name.Replace(c, '_');
                if (s.fov <= 0) s.fov = 60;
                if (s.w <= 0) s.w = 1600;
                if (s.h <= 0) s.h = 900;
                if (s.near <= 0) s.near = 0.03f;
                if (s.far <= 0) s.far = 1000f;
                if (s.w > 8192 || s.h > 8192) throw new ArgumentException("shot " + s.name + ": max 8192 px per side");
                Vec(s.pos, "pos");
                Vec(s.look, "look");
            }
            return wrap.shots;
        }

        [Serializable]
        sealed class ShotList { public Shot[] shots; }

        static Camera capCam;

        /// <summary>
        /// The one persistent capture camera. It is created once (DontSave, camera component disabled)
        /// and reused: destroying a camera right after Camera.Render() has crashed the editor, so these
        /// tools never destroy it. WorldAudit lists it as a leftover; delete it by hand when done.
        /// </summary>
        public static Camera CapCam()
        {
            if (capCam != null) return capCam;
            foreach (var c in Resources.FindObjectsOfTypeAll<Camera>())
            {
                // Not scene.IsValid(): a DontSave camera outlives NewScene/OpenScene but no longer reports a valid scene.
                if (c != null && c.name == CapCamName && !UnityEditor.EditorUtility.IsPersistent(c))
                {
                    capCam = c;
                    return capCam;
                }
            }
            var go = new GameObject(CapCamName) { hideFlags = HideFlags.DontSave };
            capCam = go.AddComponent<Camera>();
            capCam.enabled = false;
            return capCam;
        }

        internal static void Aim(Camera cam, Shot s)
        {
            var pos = s.Pos;
            var dir = s.Look - pos;
            cam.transform.position = pos;
            cam.transform.rotation = dir.sqrMagnitude < 1e-12f ? Quaternion.identity
                : Quaternion.LookRotation(dir, Mathf.Abs(Vector3.Dot(dir.normalized, Vector3.up)) > 0.999f ? Vector3.forward : Vector3.up);
            cam.fieldOfView = s.fov;
            cam.aspect = (float)s.w / s.h;
            cam.nearClipPlane = s.near;
            cam.farClipPlane = s.far;
            // Review renders show the scene as it is: baked occlusion data still holds moved static renderers at their
            // old bounds, so with culling on a moved picture or prop vanishes whenever its old spot is out of view.
            cam.useOcclusionCulling = false;
        }

        /// <summary>Absolute output directory; relative paths are taken from the project folder.</summary>
        public static string OutDir(string outDir)
        {
            if (string.IsNullOrWhiteSpace(outDir)) throw new ArgumentException("outDir is empty");
            var full = Path.GetFullPath(Path.IsPathRooted(outDir) ? outDir : Path.Combine(Directory.GetCurrentDirectory(), outDir));
            Directory.CreateDirectory(full);
            return full;
        }

        /// <summary>Reads the active render texture into a CPU texture (caller destroys it).</summary>
        internal static Texture2D ReadBack(RenderTexture rt)
        {
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGBA32, false, false);
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0, false);
            tex.Apply(false);
            RenderTexture.active = prev;
            return tex;
        }

        internal static double Percentile(List<double> sorted, double p)
        {
            if (sorted.Count == 0) return double.NaN;
            double idx = p * (sorted.Count - 1);
            int lo = (int)Math.Floor(idx), hi = (int)Math.Ceiling(idx);
            return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
        }
    }
}
