using UdonSharp;
using UnityEngine;

/// <summary>
/// The one place that decides what a plush screams and how soon it can scream again. Every FumoScream reads this
/// object, so swapping the scream is one field: assign another clip to <c>scream</c>.
/// </summary>
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class FumoScreamSettings : UdonSharpBehaviour
{
    [Tooltip("Clip every plush plays when it is put into a fire.")]
    public AudioClip scream;

    [Range(0f, 1f)]
    public float volume = 1f;

    [Tooltip("Seconds after the clip ends before the plush can scream again.")]
    public float cooldownAfterEnd = 2.5f;
}
