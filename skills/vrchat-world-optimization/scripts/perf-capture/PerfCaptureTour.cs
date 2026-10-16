// AWDK perf capture tour: TEST BUILDS ONLY. Never ship.
// Copied into a project by the client-capture procedure (references/client-capture.md), placed on a
// GameObject named "AWDK_PerfCapture" and removed again after the run. PerfCaptureGuard blocks any
// SDK build that contains it unless the capture runner set its test-build flag.
//
// On load it teleports the LOCAL player through `viewpoints` (position + yaw from each Transform),
// waits `settleSeconds`, then holds for `measureSeconds` while logging markers to the VRChat output
// log. An external frame-time logger (PresentMon) records the frames; parse_capture.py joins the two
// by wall-clock time. The Udon frame-time summary per viewpoint is a cross-check only.

using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class PerfCaptureTour : UdonSharpBehaviour
{
    public Transform[] viewpoints;
    public string runLabel = "run";
    public float startDelaySeconds = 25f;
    public float settleSeconds = 6f;
    public float measureSeconds = 20f;
    public int loops = 1;

    private int _index;
    private int _loop;
    private bool _measuring;
    private int _frames;
    private float _sum;
    private float _max;
    private float _windowStart;

    void Start()
    {
        Debug.Log("[AWDK_PERF] ready label=" + runLabel + " viewpoints=" + viewpoints.Length);
        SendCustomEventDelayedSeconds(nameof(_Next), startDelaySeconds);
    }

    public void _Next()
    {
        if (_index >= viewpoints.Length)
        {
            _index = 0;
            _loop++;
        }
        if (_loop >= loops)
        {
            Debug.Log("[AWDK_PERF] done label=" + runLabel);
            return;
        }
        Transform vp = viewpoints[_index];
        VRCPlayerApi local = Networking.LocalPlayer;
        if (Utilities.IsValid(local) && vp != null)
        {
            local.TeleportTo(vp.position, Quaternion.Euler(0f, vp.eulerAngles.y, 0f));
        }
        Debug.Log("[AWDK_PERF] goto " + vp.name + " loop=" + _loop);
        SendCustomEventDelayedSeconds(nameof(_Begin), settleSeconds);
    }

    public void _Begin()
    {
        _frames = 0;
        _sum = 0f;
        _max = 0f;
        _windowStart = Time.realtimeSinceStartup;
        _measuring = true;
        Debug.Log("[AWDK_PERF] begin " + viewpoints[_index].name + " loop=" + _loop);
        SendCustomEventDelayedSeconds(nameof(_End), measureSeconds);
    }

    public void _End()
    {
        _measuring = false;
        float span = Time.realtimeSinceStartup - _windowStart;
        float avgMs = _frames > 0 ? 1000f * _sum / _frames : 0f;
        Debug.Log("[AWDK_PERF] end " + viewpoints[_index].name + " loop=" + _loop
            + " frames=" + _frames + " seconds=" + span.ToString("F2")
            + " udonAvgMs=" + avgMs.ToString("F3") + " udonMaxMs=" + (1000f * _max).ToString("F3"));
        _index++;
        SendCustomEventDelayedSeconds(nameof(_Next), 0.5f);
    }

    void Update()
    {
        if (!_measuring) return;
        float dt = Time.unscaledDeltaTime;
        _frames++;
        _sum += dt;
        if (dt > _max) _max = dt;
    }
}
