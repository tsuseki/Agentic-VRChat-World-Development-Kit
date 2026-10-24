using UdonSharp;
using UnityEngine;

/// <summary>
/// Marker on a trigger collider over a fire's flame area (layer Walkthrough: only Pickup-layer objects touch it,
/// so players and hands never trigger it). FumoScream reacts to entering any collider that carries this.
/// </summary>
[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class FumoFireZone : UdonSharpBehaviour
{
}
