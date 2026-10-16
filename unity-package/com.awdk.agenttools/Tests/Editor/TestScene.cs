using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace AWDK.AgentTools.Tests
{
    /// <summary>Scene and mesh builders shared by the tests.</summary>
    static class TestScene
    {
        public static void Fresh() => EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        /// <summary>Square in the XZ plane, centred on the origin, facing +Y (or -Y when flipped).</summary>
        public static Mesh Quad(float size, bool faceDown = false)
        {
            float h = size * 0.5f;
            var m = new Mesh { name = "TestQuad" };
            m.vertices = new[] { new Vector3(-h, 0, -h), new Vector3(-h, 0, h), new Vector3(h, 0, h), new Vector3(h, 0, -h) };
            m.triangles = faceDown ? new[] { 0, 2, 1, 0, 3, 2 } : new[] { 0, 1, 2, 0, 2, 3 };
            m.RecalculateNormals();
            m.RecalculateBounds();
            return m;
        }

        /// <summary>Two separate (no shared vertices) squares in one mesh, the second shifted by +offset in X.</summary>
        public static Mesh TwoQuads(float size, float offset)
        {
            var a = Quad(size);
            var v = new List<Vector3>(a.vertices);
            foreach (var p in a.vertices) v.Add(p + new Vector3(offset, 0, 0));
            var m = new Mesh { name = "TwoQuads" };
            m.SetVertices(v);
            m.triangles = new[] { 0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7 };
            m.RecalculateNormals();
            return m;
        }

        /// <summary>size x size grid of cells in the XZ plane (origin corner), facing +Y, 2 tris per cell.</summary>
        public static Mesh Grid(int cells, float size, bool otherDiagonal)
        {
            int n = cells + 1;
            var v = new Vector3[n * n];
            float step = size / cells;
            for (int z = 0; z < n; z++)
                for (int x = 0; x < n; x++)
                    v[z * n + x] = new Vector3(x * step, 0, z * step);
            var t = new int[cells * cells * 6];
            int k = 0;
            for (int z = 0; z < cells; z++)
                for (int x = 0; x < cells; x++)
                {
                    int i0 = z * n + x, i1 = i0 + 1, i2 = i0 + n, i3 = i2 + 1;
                    if (!otherDiagonal) { t[k++] = i0; t[k++] = i2; t[k++] = i3; t[k++] = i0; t[k++] = i3; t[k++] = i1; }
                    else { t[k++] = i0; t[k++] = i2; t[k++] = i1; t[k++] = i1; t[k++] = i2; t[k++] = i3; }
                }
            var m = new Mesh { name = "Grid", indexFormat = IndexFormat.UInt32 };
            m.vertices = v;
            m.triangles = t;
            m.RecalculateNormals();
            m.RecalculateBounds();
            return m;
        }

        public static Material Unlit(Color c)
        {
            var mat = new Material(Shader.Find("Unlit/Color"));
            mat.color = c;
            return mat;
        }

        public static GameObject MeshObject(string name, Mesh mesh, Vector3 pos, Quaternion rot, Material mat = null, Transform parent = null)
        {
            var go = new GameObject(name);
            if (parent != null) go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(pos, rot);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterial = mat;
            return go;
        }

        public static GameObject MeshObject(string name, Mesh mesh, Vector3 pos, Material mat = null, Transform parent = null)
            => MeshObject(name, mesh, pos, Quaternion.identity, mat, parent);

        /// <summary>Reads "KEY=<int>" from a report.</summary>
        public static int Count(string report, string key)
        {
            var m = Regex.Match(report, Regex.Escape(key) + @"=(\d+)");
            if (!m.Success) throw new System.InvalidOperationException(key + " not in report:\n" + report);
            return int.Parse(m.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture);
        }

        /// <summary>Reads the count of an audit section line "[TITLE] n".</summary>
        public static int Section(string report, string title)
        {
            var m = Regex.Match(report, @"\[" + Regex.Escape(title) + @"\] (\d+)");
            if (!m.Success) throw new System.InvalidOperationException(title + " not in report:\n" + report);
            return int.Parse(m.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture);
        }
    }
}
