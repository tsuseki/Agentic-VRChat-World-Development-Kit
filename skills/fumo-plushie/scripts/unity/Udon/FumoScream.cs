using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
using VRC.Udon.Common.Interfaces;

/// <summary>
/// On every plush pickup. When this plush's collider ENTERS a FumoFireZone trigger the plush screams from its own
/// 3D AudioSource, so the sound follows it if it is pulled out; the clip always plays to the end. After it ends
/// the plush is quiet for settings.cooldownAfterEnd seconds; staying in the fire never retriggers, only a new
/// enter after the cooldown does.
/// Only the plush's owner (the holder) detects the enter and sends one network event to All; every client plays
/// the scream from its own copy of the plush. Sync mode NoVariableSync (no synced fields, but network events work):
/// the plush's VRCObjectSync and pickup are untouched.
/// Wired by FumoScreamBuilder (Editor).
/// </summary>
[UdonBehaviourSyncMode(BehaviourSyncMode.NoVariableSync)] // None would forbid SendCustomNetworkEvent
public class FumoScream : UdonSharpBehaviour
{
    public FumoScreamSettings settings;

    [Tooltip("3D AudioSource on this plush.")]
    public AudioSource voice;

    private float _cooldownUntil;
    private float _sendLockUntil;

    void OnTriggerEnter(Collider other)
    {
        if (other == null) return;
        if (other.GetComponent<FumoFireZone>() == null) return;
        EnteredFire();
    }

    /// <summary>The plush entered a fire (the owner's client only sends).</summary>
    public void EnteredFire()
    {
        if (!Networking.IsOwner(gameObject)) return;

        float now = Time.time;
        if (now < _cooldownUntil || now < _sendLockUntil) return;
        if (voice != null && voice.isPlaying) return;

        _sendLockUntil = now + 0.5f;
        SendCustomNetworkEvent(NetworkEventTarget.All, nameof(Scream));
    }

    /// <summary>Network event: runs on every client.</summary>
    public void Scream()
    {
        if (settings == null || settings.scream == null || voice == null) return;
        if (voice.isPlaying || Time.time < _cooldownUntil) return;

        voice.clip = settings.scream;
        voice.volume = settings.volume;
        voice.Play();
        _cooldownUntil = Time.time + settings.scream.length + settings.cooldownAfterEnd;
    }
}
