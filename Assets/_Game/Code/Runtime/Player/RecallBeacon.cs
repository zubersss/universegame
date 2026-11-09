using System.Collections.Generic;
using Meridian.Art;
using Meridian.Mining;
using Meridian.Progress;
using Meridian.Rendering;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>
    /// U-176 (D1_TABLES §4 "Climbing", asc_recall, B-210's recall_beacon): the recall beacon. R under the Surface Line plants it beside the feet
    /// (its pulse clip while it waits); after the tables' 5 s it lifts off and the surveyor wakes topside where a conk-out would (the last base
    /// piece, else beside the ship) with the pack kept. One charge a run (asc_recall's beacons), refilled on reaching topside.
    /// </summary>
    public sealed class RecallBeacon : MonoBehaviour
    {
        public const string Key = "props/dig/recall_beacon";
        /// <summary>B-210's clips: pulse frames 0..3 (looped while it waits), liftoff 4..9 (the last half second), 12 fps.</summary>
        public const int PulseFrames = 4, LiftFrames = 6;
        public const float Fps = 12f;
        /// <summary>The beacon stands this far behind the surveyor (m).</summary>
        public const float PlantBehind = 0.6f;

        public PlayerController controller;
        public ConkOut conkOut;
        public TerrainStreamer terrain;

        /// <summary>Beacons used this run; left now; waiting to lift; seconds until it does.</summary>
        public int Used { get; private set; }
        public int Left => Mathf.Max(0, SkillStats.RecallBeacons - Used);
        public bool Waiting { get; private set; }
        public float Remaining => Waiting ? Mathf.Max(0f, Ascent.RecallSeconds - waited) : 0f;
        public Vector2 Planted { get; private set; }
        /// <summary>Raised when the beacon lifts the surveyor, with where it set them down.</summary>
        public event System.Action<Vector2> Recalled;

        InputAction recall;
        SpriteRenderer beacon;
        /// <summary>The planted beacon's drawing (tests, captures).</summary>
        public SpriteRenderer Beacon => beacon;
        Sprite[] frames;
        AsyncOperationHandle<IList<Sprite>> handle;
        float waited;

        void Awake()
        {
            if (controller == null) controller = GetComponent<PlayerController>();
            var go = new GameObject("RecallBeacon");
            beacon = go.AddComponent<SpriteRenderer>();
            beacon.sortingOrder = 5;
            beacon.enabled = false;
        }

        void Start()
        {
            if (controller != null && controller.actions != null && !controller.externalInput)
                recall = controller.actions.FindActionMap(MeridianInput.OnFoot, true).FindAction("Recall", false);
        }

        void OnDestroy()
        {
            if (handle.IsValid()) ArtLoad.Release(handle);
            if (beacon != null) Destroy(beacon.gameObject);
        }

        Vector2 Feet => controller != null && controller.Body != null ? controller.Body.position : (Vector2)transform.position;

        /// <summary>Plants the beacon (false: none left this run, one already waiting, or already topside).</summary>
        public bool Activate()
        {
            if (Waiting || Left <= 0 || terrain == null || DigRun.Topside(terrain, Feet)) return false;
            Used++;
            Waiting = true;
            waited = 0f;
            // beside the feet, behind the surveyor (B-210's pole is thin: under the body it would not read)
            Planted = Feet + new Vector2(-(controller != null ? controller.Facing : 1) * PlantBehind, 0f);
            beacon.transform.position = new Vector3(Planted.x, Planted.y, 0f);
            if (frames == null && !handle.IsValid())
            {
                handle = ArtLoad.Asset<IList<Sprite>>(Key);
                handle.Completed += op =>
                {
                    if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    var list = new List<Sprite>(op.Result);
                    list.Sort((a, b) => JetpackOverlay.FrameOf(a).CompareTo(JetpackOverlay.FrameOf(b)));
                    frames = list.ToArray();
                    var mat = ArtMaterials.MaterialFor(Key);
                    if (mat != null) beacon.sharedMaterial = mat;
                };
            }
            return true;
        }

        void Update()
        {
            if (recall != null && recall.WasPressedThisFrame()) Activate();
            if (!Waiting)
            {
                // the run ends topside: the charge refills
                if (Used > 0 && terrain != null && DigRun.Topside(terrain, Feet)) Used = 0;
                return;
            }
            waited += Time.deltaTime;
            float total = Ascent.RecallSeconds, lift = LiftFrames / Fps;
            if (frames != null && frames.Length > 0)
            {
                int f = waited < total - lift
                    ? (int)(waited * Fps) % PulseFrames
                    : PulseFrames + Mathf.Min(LiftFrames - 1, (int)((waited - (total - lift)) * Fps));
                beacon.sprite = frames[Mathf.Min(f, frames.Length - 1)];
                beacon.enabled = true;
            }
            if (waited >= total) Lift();
        }

        void Lift()
        {
            Waiting = false;
            beacon.enabled = false;
            var to = conkOut != null ? conkOut.WakePoint(out _) : Feet;
            if (controller != null && controller.Body != null)
            {
                var g = controller.GetComponent<GrappleLine>();
                if (g != null) g.Release();
                controller.Body.position = to;
                controller.transform.position = to;
                controller.Body.linearVelocity = Vector2.zero;
            }
            Recalled?.Invoke(to);
        }
    }
}
