using UnityEngine;

namespace AWDK.AgentTools.TestFakes
{
    /// <summary>Stand-in with the VRChat SDK type name and the two members WorldAudit reads.</summary>
    public class VRCPickup : MonoBehaviour
    {
        public enum AutoHoldMode { AutoDetect, Yes, No }

        public float proximity = 2f;
        public AutoHoldMode AutoHold = AutoHoldMode.AutoDetect;
    }
}
