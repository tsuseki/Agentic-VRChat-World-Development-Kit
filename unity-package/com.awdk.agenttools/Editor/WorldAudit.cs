using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;

namespace AWDK.AgentTools
{
    /// <summary>
    /// Read-only world audit. One synchronous call; returns a sectioned report ending "ISSUES=&lt;n&gt;".
    /// VRChat SDK types are matched by name through reflection, so the package compiles without the SDK.
    /// </summary>
    public static class WorldAudit
    {
        /// <summary>Entries listed per section (counts are always exact).</summary>
        public static int MaxPerSection = 40;
        /// <summary>Textures whose larger side is at most this many pixels are not reported as uncompressed.</summary>
        public static int MinTextureSize = 64;

        static readonly Regex PropRoot = new Regex(@"(^|[^a-z])(props?|dressing|furniture|decor|clutter)([^a-z]|$)", RegexOptions.IgnoreCase);
        static readonly Regex WalkName = new Regex(@"floor|ground|stair|step|ramp|terrain|walk|path|road|deck|platform|landing", RegexOptions.IgnoreCase);

        /// <summary>Name of the off-by-default BoxCollider on a bed/couch top surface (switched on by the world lie-down toggle).</summary>
        public const string LieDownName = "LieDownCollider";
        /// <summary>Name of the always-on BoxCollider on big furniture (dining/kitchen tables, counters, cabinets, wardrobes).</summary>
        public const string SolidName = "SolidCollider";
        /// <summary>Name of a containment guard shell (MeshCollider): upright guard slabs along open walk edges whose
        /// thin tops add up to walkable-angle area but are never walked. Not a floor; counted on [CONTAINMENT_SHELLS].
        /// Any other floor-like MeshCollider is still flagged.</summary>
        public const string ContainName = "ContainShell";

        sealed class Section
        {
            public readonly string Title, Hint;
            public readonly List<string> Items = new List<string>();
            public int Info;
            public Section(string title, string hint) { Title = title; Hint = hint; }
        }

        public static string Run(string rootPath = null)
        {
            var roots = Util.ResolveRoots(rootPath);
            if (!string.IsNullOrEmpty(rootPath) && roots.Count == 0) return "ERROR root not found in any loaded scene: " + rootPath;

            var stations = new Section("STATIONS", "VRCStation / VRC_Station components: remove unless the user asked for a seat");
            var pickups = new Section("PICKUPS", "VRC_Pickup with proximity != 0.1 or AutoHold != No");
            var lights = new Section("REALTIME_OR_MIXED_LIGHTS", "lights that are not Baked (cost every frame in VRChat)");
            var leftovers = new Section("LEFTOVER_OBJECTS", "__name__ helper objects (captures, probes, temp tools): delete before upload");
            var walkMesh = new Section("WALKABLE_MESHCOLLIDERS", "MeshCollider on a floor-like surface: use BoxColliders / one smooth ramp box");
            var propCols = new Section("PROP_COLLIDERS", "colliders under Props/Dressing/Furniture roots: props are walk-through unless they must block");
            var uv2 = new Section("STATIC_MISSING_UV2", "ContributeGI renderers lightmapped without UV2: enable Generate Lightmap UVs");
            var tex = new Section("UNCOMPRESSED_TEXTURES", "textures on scene materials stored uncompressed (VRAM / download size)");

            var seenTex = new HashSet<Texture>();
            int lieDownOff = 0, solidOn = 0, containShells = 0;
            foreach (var root in roots)
            {
                foreach (var tr in root.GetComponentsInChildren<Transform>(true))
                {
                    var go = tr.gameObject;
                    string path = Util.PathOf(tr);
                    string state = go.activeInHierarchy ? "" : " (inactive)";
                    if (Util.IsEditorOnly(tr)) state += " (EditorOnly)";

                    if (go.name.Length > 4 && go.name.StartsWith("__", StringComparison.Ordinal) && go.name.EndsWith("__", StringComparison.Ordinal))
                    {
                        if ((go.hideFlags & HideFlags.DontSave) != 0) { leftovers.Info++; }
                        else leftovers.Items.Add(path + state);
                    }

                    foreach (var c in go.GetComponents<Component>())
                    {
                        if (c == null) continue; // missing script
                        var type = c.GetType();
                        if (Util.TypeNamed(type, "VRCStation", "VRC_Station"))
                            stations.Items.Add(path + " [" + type.FullName + "]" + state);
                        else if (Util.TypeNamed(type, "VRCPickup", "VRC_Pickup"))
                        {
                            var prox = Member(c, "proximity");
                            var hold = Member(c, "AutoHold");
                            float p = prox == null ? float.NaN : Convert.ToSingle(prox, Util.Inv);
                            string h = hold?.ToString() ?? "?";
                            if (float.IsNaN(p) || Mathf.Abs(p - 0.1f) > 1e-4f || h != "No")
                                pickups.Items.Add(string.Format(Util.Inv, "{0} proximity={1} AutoHold={2}{3}", path, prox == null ? "?" : p.ToString("0.###", Util.Inv), h, state));
                        }
                    }

                    var light = go.GetComponent<Light>();
                    if (light != null && light.enabled && light.lightmapBakeType != LightmapBakeType.Baked)
                        lights.Items.Add(string.Format(Util.Inv, "{0} type={1} mode={2} intensity={3:0.##} shadows={4}{5}",
                            path, light.type, light.lightmapBakeType, light.intensity, light.shadows, state));

                    var propRoot = PropAncestor(tr);
                    bool lieDown = propRoot != null && go.name == LieDownName;
                    bool solid = propRoot != null && go.name == SolidName;
                    foreach (var col in go.GetComponents<Collider>())
                    {
                        if (lieDown)
                        {
                            // The one allowed prop collider: a BoxCollider that ships off (inactive or disabled)
                            // and is switched on by the world's lie-down toggle.
                            bool off = !go.activeSelf || !col.enabled;
                            if (col is BoxCollider && off && !col.isTrigger) lieDownOff++;
                            else propCols.Items.Add(string.Format(Util.Inv, "{0} [{1}] under '{2}' ({3}){4}", path, col.GetType().Name, propRoot.name,
                                !(col is BoxCollider) ? "LieDownCollider must be a BoxCollider" : col.isTrigger ? "LieDownCollider must not be a trigger" : "LieDownCollider must be off by default", state));
                            continue;
                        }
                        if (solid)
                        {
                            // Big furniture blocks players and holds pickups: one enabled, non-trigger BoxCollider.
                            bool on = go.activeInHierarchy && col.enabled;
                            if (col is BoxCollider && on && !col.isTrigger) solidOn++;
                            else propCols.Items.Add(string.Format(Util.Inv, "{0} [{1}] under '{2}' ({3}){4}", path, col.GetType().Name, propRoot.name,
                                !(col is BoxCollider) ? "SolidCollider must be a BoxCollider" : col.isTrigger ? "SolidCollider must not be a trigger" : "SolidCollider must be on", state));
                            continue;
                        }
                        if (!col.enabled || col.isTrigger) continue;
                        if (col is MeshCollider mc && IsWalkable(mc, out string why))
                        {
                            if (go.name == ContainName && propRoot == null) containShells++;
                            else walkMesh.Items.Add(path + " (" + why + ")" + state);
                        }
                        if (propRoot != null && !HasPickup(tr))
                            propCols.Items.Add(string.Format(Util.Inv, "{0} [{1}] under '{2}'{3}", path, col.GetType().Name, propRoot.name, state));
                    }

                    var mr = go.GetComponent<MeshRenderer>();
                    if (mr != null)
                    {
                        var flags = GameObjectUtility.GetStaticEditorFlags(go);
                        var mf = go.GetComponent<MeshFilter>();
                        var mesh = mf != null ? mf.sharedMesh : null;
                        if ((flags & StaticEditorFlags.ContributeGI) != 0 && mr.receiveGI == ReceiveGI.Lightmaps
                            && mesh != null && !mesh.HasVertexAttribute(VertexAttribute.TexCoord1))
                            uv2.Items.Add(string.Format(Util.Inv, "{0} mesh={1}{2}", path, mesh.name, state));
                    }
                    var rend = go.GetComponent<Renderer>();
                    if (rend != null)
                        foreach (var mat in rend.sharedMaterials)
                        {
                            if (mat == null) continue;
                            foreach (var prop in mat.GetTexturePropertyNames())
                            {
                                if (!(mat.GetTexture(prop) is Texture2D t2) || !seenTex.Add(t2)) continue;
                                if (Mathf.Max(t2.width, t2.height) <= MinTextureSize) continue;
                                if (GraphicsFormatUtility.IsCompressedFormat(t2.graphicsFormat)) continue;
                                string assetPath = AssetDatabase.GetAssetPath(t2);
                                var imp = AssetImporter.GetAtPath(assetPath) as TextureImporter;
                                tex.Items.Add(string.Format(Util.Inv, "{0} {1}x{2} format={3} compression={4} (material {5}, first seen on {6})",
                                    string.IsNullOrEmpty(assetPath) ? t2.name + " <not an asset>" : assetPath, t2.width, t2.height, t2.graphicsFormat,
                                    imp != null ? imp.textureCompression.ToString() : "-", mat.name, path));
                            }
                        }
                }
            }

            var sections = new[] { stations, pickups, lights, leftovers, walkMesh, propCols, uv2, tex };
            var sb = new StringBuilder();
            sb.AppendLine(string.Format(Util.Inv, "WORLD AUDIT scenes={0} root={1}", Util.SceneNames(), string.IsNullOrEmpty(rootPath) ? "<all>" : rootPath));
            int issues = 0;
            foreach (var s in sections)
            {
                issues += s.Items.Count;
                sb.AppendLine(string.Format(Util.Inv, "[{0}] {1}  -- {2}", s.Title, s.Items.Count, s.Hint));
                for (int i = 0; i < s.Items.Count && i < MaxPerSection; i++) sb.AppendLine("  " + s.Items[i]);
                if (s.Items.Count > MaxPerSection) sb.AppendLine("  ... " + (s.Items.Count - MaxPerSection) + " more");
                if (s.Info > 0) sb.AppendLine(string.Format(Util.Inv, "  ({0} more are DontSave and will not be saved or uploaded)", s.Info));
                if (s == walkMesh && containShells > 0)
                    sb.AppendLine(string.Format(Util.Inv, "[CONTAINMENT_SHELLS] {0}  -- info: '{1}' guard-slab MeshColliders (thin guard tops, not floors)", containShells, ContainName));
                if (s == propCols)
                {
                    sb.AppendLine(string.Format(Util.Inv, "[LIE_DOWN_COLLIDERS] {0}  -- info: lie-down colliders: {0}, all off by default (enabled by the world lie-down toggle)", lieDownOff));
                    sb.AppendLine(string.Format(Util.Inv, "[SOLID_FURNITURE_COLLIDERS] {0}  -- info: solid colliders on big furniture: {0}, all on", solidOn));
                }
            }
            sb.Append("ISSUES=").Append(issues.ToString(Util.Inv));
            return sb.ToString();
        }

        static object Member(Component c, string name)
        {
            const BindingFlags bf = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
            for (var t = c.GetType(); t != null; t = t.BaseType)
            {
                var f = t.GetField(name, bf);
                if (f != null) return f.GetValue(c);
                var p = t.GetProperty(name, bf);
                if (p != null && p.CanRead && p.GetIndexParameters().Length == 0) return p.GetValue(c);
            }
            return null;
        }

        static Transform PropAncestor(Transform t)
        {
            for (var p = t.parent; p != null; p = p.parent)
                if (PropRoot.IsMatch(p.name)) return p;
            return null;
        }

        static bool HasPickup(Transform t)
        {
            for (var p = t; p != null; p = p.parent)
                foreach (var c in p.GetComponents<Component>())
                    if (c != null && Util.TypeNamed(c.GetType(), "VRCPickup", "VRC_Pickup")) return true;
            return false;
        }

        /// <summary>Floor-like: a walk-ish name, or at least 1 m² of upward-facing (normal.y &gt; 0.7) area.</summary>
        static bool IsWalkable(MeshCollider mc, out string why)
        {
            why = null;
            if (WalkName.IsMatch(mc.gameObject.name)) { why = "name"; return true; }
            var mesh = mc.sharedMesh;
            if (mesh == null) return false;
            if (mesh.vertexCount > 300000) { why = "large mesh, not analysed"; return mc.bounds.size.x * mc.bounds.size.z >= 1f; }
            var m = mc.transform.localToWorldMatrix;
            var v = mesh.vertices;
            var idx = mesh.triangles;
            float sign = m.determinant < 0 ? -1f : 1f;
            float up = 0;
            for (int i = 0; i + 2 < idx.Length; i += 3)
            {
                var a = m.MultiplyPoint3x4(v[idx[i]]);
                var cr = Vector3.Cross(m.MultiplyPoint3x4(v[idx[i + 1]]) - a, m.MultiplyPoint3x4(v[idx[i + 2]]) - a);
                float area2 = cr.magnitude;
                if (area2 < 1e-12f) continue;
                if (sign * cr.y / area2 > 0.7f) up += area2;
            }
            up *= 0.5f;
            if (up >= 1f) { why = string.Format(Util.Inv, "{0:0.#} m2 walkable-angle area", up); return true; }
            return false;
        }
    }
}
