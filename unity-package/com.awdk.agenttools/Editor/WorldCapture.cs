using System;
using System.Collections;
using System.IO;
using System.Text;
using UnityEngine;

namespace AWDK.AgentTools
{
    /// <summary>
    /// Renders review screenshots from the one persistent __CapCam__ (created on first use, never
    /// destroyed, camera component kept disabled, no lights added). One shot per editor tick.
    /// Output: &lt;outDir&gt;/&lt;name&gt;.png. Uses the scene's lighting, lightmaps and skybox as they are.
    /// </summary>
    public static class WorldCapture
    {
        public const string Kind = "WorldCapture";
        /// <summary>MSAA samples for captures (1, 2, 4 or 8).</summary>
        public static int Msaa = 8;

        /// <summary>
        /// shotsJson: [{"name":"01_wide","pos":[x,y,z],"look":[x,y,z],"fov":60,"w":1600,"h":900}]
        /// (optional "near"/"far"). Poll <see cref="Status"/> until the report ends with "COMPLETE".
        /// </summary>
        public static string Shoot(string outDir, string shotsJson)
        {
            string dir; Shot[] shots;
            try { dir = Util.OutDir(outDir); shots = Util.ParseShots(shotsJson); }
            catch (Exception e) { return "ERROR " + e.Message; }
            JobRunner.Start(Kind, job => Run(job, dir, shots));
            return string.Format(Util.Inv, "STARTED WorldCapture shots={0} out={1}; poll WorldCapture.Status()", shots.Length, dir);
        }

        public static string Status() => JobRunner.Status(Kind);

        /// <summary>Runs to completion on the calling thread (tests / scripts).</summary>
        public static string ShootBlocking(string outDir, string shotsJson, double maxSeconds = 120)
        {
            string dir; Shot[] shots;
            try { dir = Util.OutDir(outDir); shots = Util.ParseShots(shotsJson); }
            catch (Exception e) { return "ERROR " + e.Message; }
            return JobRunner.RunBlocking(JobRunner.Create(Kind, job => Run(job, dir, shots)), maxSeconds);
        }

        static IEnumerator Run(AgentJob job, string dir, Shot[] shots)
        {
            var sb = new StringBuilder();
            var cam = Util.CapCam();
            for (int i = 0; i < shots.Length; i++)
            {
                var s = shots[i];
                job.Progress = string.Format(Util.Inv, "shot {0}/{1} {2}", i + 1, shots.Length, s.name);
                var file = Path.Combine(dir, s.name + ".png");
                File.WriteAllBytes(file, RenderPng(cam, s));
                sb.AppendLine(string.Format(Util.Inv, "{0}: {1}x{2} fov={3} pos={4} look={5} -> {6}",
                    s.name, s.w, s.h, s.fov, Util.F3(s.Pos), Util.F3(s.Look), file));
                yield return null;
            }
            sb.Append(string.Format(Util.Inv, "SHOTS={0} COMPLETE", shots.Length));
            job.Result = sb.ToString();
        }

        static byte[] RenderPng(Camera cam, Shot s)
        {
            var msaaRt = RenderTexture.GetTemporary(new RenderTextureDescriptor(s.w, s.h, RenderTextureFormat.ARGB32, 24)
                { sRGB = true, msaaSamples = Mathf.Clamp(Mathf.ClosestPowerOfTwo(Msaa), 1, 8) });
            var rt = RenderTexture.GetTemporary(new RenderTextureDescriptor(s.w, s.h, RenderTextureFormat.ARGB32, 0) { sRGB = true, msaaSamples = 1 });
            try
            {
                Util.Aim(cam, s);
                cam.allowMSAA = true;
                cam.allowHDR = true;
                cam.clearFlags = CameraClearFlags.Skybox;
                cam.targetTexture = msaaRt;
                cam.Render();
                Graphics.Blit(msaaRt, rt); // resolves MSAA
                var tex = Util.ReadBack(rt);
                try { return tex.EncodeToPNG(); }
                finally { UnityEngine.Object.DestroyImmediate(tex); }
            }
            finally
            {
                cam.targetTexture = null;
                RenderTexture.ReleaseTemporary(msaaRt);
                RenderTexture.ReleaseTemporary(rt);
            }
        }
    }
}
