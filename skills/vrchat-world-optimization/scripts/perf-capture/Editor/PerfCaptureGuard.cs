// AWDK perf capture guard. Blocks every VRChat SDK build of a scene that still contains a
// PerfCaptureTour unless the capture runner opted in for this one Build & Test via
// PerfCaptureGuard.AllowTestBuild(). An upload always starts with a build, so a forgotten harness
// can never be uploaded. Copy into the project's Editor folder together with PerfCaptureTour.cs;
// keep it there permanently (it is harmless without a harness).

using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using VRC.SDKBase.Editor.BuildPipeline;

public class PerfCaptureGuard : IVRCSDKBuildRequestedCallback
{
    const string Key = "AWDK_PerfCapture_AllowTestBuild";

    public int callbackOrder => -1000;

    /// Call right before builder.BuildAndTest(); the permission is consumed by that one build.
    public static void AllowTestBuild() => SessionState.SetBool(Key, true);

    public bool OnBuildRequested(VRCSDKRequestedBuildType requestedBuildType)
    {
        if (requestedBuildType != VRCSDKRequestedBuildType.Scene) return true;
        bool allowed = SessionState.GetBool(Key, false);
        SessionState.EraseBool(Key);
        if (!HarnessPresent()) return true;
        if (allowed)
        {
            Debug.LogWarning("[AWDK_PERF] Build contains the perf capture harness (allowed once for Build & Test).");
            return true;
        }
        Debug.LogError("[AWDK_PERF] Build blocked: the scene contains the perf capture harness (AWDK_PerfCapture). Remove it before building or uploading.");
        return false;
    }

    static bool HarnessPresent()
    {
        for (int s = 0; s < SceneManager.sceneCount; s++)
        {
            var scene = SceneManager.GetSceneAt(s);
            if (!scene.isLoaded) continue;
            foreach (var root in scene.GetRootGameObjects())
            {
                foreach (var t in root.GetComponentsInChildren<Transform>(true))
                    if (t.name == "AWDK_PerfCapture") return true;
                // Udon programs: match the program asset name (UdonBehaviour.programSource).
                foreach (var b in root.GetComponentsInChildren<MonoBehaviour>(true))
                {
                    if (b == null) continue;
                    if (b.GetType().Name == "PerfCaptureTour") return true;
                    if (b.GetType().Name != "UdonBehaviour") continue;
                    var src = new SerializedObject(b).FindProperty("programSource");
                    if (src != null && src.objectReferenceValue != null &&
                        src.objectReferenceValue.name.Contains("PerfCaptureTour")) return true;
                }
            }
        }
        return false;
    }
}
