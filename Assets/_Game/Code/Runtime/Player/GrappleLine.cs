using System.Collections.Generic;
using Meridian.Art;
using Meridian.Progress;
using Meridian.Rendering;
using Meridian.Rig;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>
    /// U-176 (Bible 5.2 §8.1, D1_TABLES §4 "Climbing", B-210's grapple_hook / reel_up): the Grapple. Its left click fires the hook from the
    /// hands toward the aim at the tables' 40 m/s; it catches the first ground along the line (12 m; asc_grapple_2 24, _3 40) or falls back.
    /// Held, the line reels the surveyor to the hook at 4 m/s × the reel stat × the pack's load (the planet's g cancelled), and hangs there
    /// (0.9 m under it); letting go of the button or a jump lets go. asc_grapple_3's two anchors: the right click fires a second hook while
    /// the first holds, which takes over when it catches (no drop between hops). PlayerController asks it for the pull every fixed step.
    /// </summary>
    public sealed class GrappleLine : MonoBehaviour
    {
        public const string HookKey = "props/dig/grapple_hook";
        /// <summary>Where the line meets the hook (B-210's line_socket, metres in the hook's frame: its +y along the throw).</summary>
        public static readonly Vector2 HookLineSocket = new Vector2(0f, -0.42f);
        public const float LineWidth = 0.045f;
        static readonly Color Ink = new Color(0.13f, 0.10f, 0.08f, 1f);

        public PlayerController controller;
        public RigToolView tool;

        /// <summary>The button holds the line (PlayerRigInput sets it every frame).</summary>
        [System.NonSerialized] public bool held;

        /// <summary>A hook holds the surveyor; one is in flight; where the holding hook is; where the flying one is headed and whether
        /// it will catch.</summary>
        public bool Attached { get; private set; }
        public bool Flying { get; private set; }
        public Vector2 Anchor { get; private set; }
        public Vector2 FlightTo { get; private set; }
        public bool FlightHits { get; private set; }
        /// <summary>The reel reached the hook: the surveyor hangs under it.</summary>
        public bool AtHook { get; private set; }
        /// <summary>Reeling now (attached, held, short of the hook): the reel_up clip.</summary>
        public bool Reeling => Attached && held && !AtHook;
        public int Fired { get; private set; }
        public int Caught { get; private set; }

        Vector2 flightFrom;
        float flightT, flightFor;
        SpriteRenderer hook;
        LineRenderer line;
        AsyncOperationHandle<IList<Sprite>> handle;
        readonly RaycastHit2D[] hits = new RaycastHit2D[8];

        void Awake()
        {
            if (controller == null) controller = GetComponent<PlayerController>();
            var go = new GameObject("GrappleHook");
            go.transform.SetParent(transform, false);
            hook = go.AddComponent<SpriteRenderer>();
            hook.sortingOrder = Meridian.View2D.SpriteCharacterView.SurveyorOrder + 1; // U-200: over the drawn surveyor
            hook.enabled = false;
            var lgo = new GameObject("GrappleLine");
            lgo.transform.SetParent(transform, false);
            line = lgo.AddComponent<LineRenderer>();
            line.useWorldSpace = true;
            line.positionCount = 2;
            line.startWidth = line.endWidth = LineWidth;
            line.startColor = line.endColor = Ink;
            line.numCapVertices = 0;
            line.sortingOrder = Meridian.View2D.SpriteCharacterView.SurveyorOrder + 1;
            line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            line.receiveShadows = false;
            var unlit = ArtMaterials.Active != null ? ArtMaterials.Active.unlit : null;
            if (unlit != null) line.sharedMaterial = unlit;
            line.enabled = false;
            handle = ArtLoad.Asset<IList<Sprite>>(HookKey);
            handle.Completed += op =>
            {
                if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                hook.sprite = op.Result[0];
                var mat = ArtMaterials.MaterialFor(HookKey);
                if (mat != null) hook.sharedMaterial = mat;
            };
        }

        void OnDestroy() { if (handle.IsValid()) ArtLoad.Release(handle); }

        Vector2 Feet => controller != null && controller.Body != null ? controller.Body.position : (Vector2)transform.position;
        /// <summary>The line's end in the hands (the reel's pull point).</summary>
        public Vector2 Hands => Feet + new Vector2(0f, Ascent.HandsUp);

        /// <summary>
        /// Throws the hook from the hands toward `aim` (false before asc_grapple_1). A hook already holding lets go first, unless a second
        /// anchor is bought (asc_grapple_3): then it holds until the new one catches.
        /// </summary>
        public bool Fire(Vector2 aim)
        {
            float length = SkillStats.GrappleM;
            var from = Hands;
            var d = aim - from;
            if (length <= 0f || d.sqrMagnitude < 1e-4f) return false;
            d.Normalize();
            if (Attached && SkillStats.GrappleAnchors < 2) Release();
            FlightHits = Cast(from, d, length, out var to);
            flightFrom = from;
            FlightTo = to;
            flightT = 0f;
            flightFor = Vector2.Distance(from, to) / Mathf.Max(1f, Ascent.HookSpeed);
            Flying = true;
            Fired++;
            return true;
        }

        /// <summary>Lets go: the line and any hook in flight.</summary>
        public void Release()
        {
            Attached = Flying = AtHook = false;
        }

        /// <summary>The first ground (a terrain collider, triggers aside) along the throw within `length`, else the throw's end.</summary>
        bool Cast(Vector2 from, Vector2 dir, float length, out Vector2 point)
        {
            var filter = new ContactFilter2D { useTriggers = false };
            int n = Physics2D.Raycast(from, dir, filter, hits, length);
            float best = float.MaxValue;
            point = from + dir * length;
            bool found = false;
            for (int i = 0; i < n; i++)
            {
                var h = hits[i];
                if (h.collider == null || h.collider.GetComponentInParent<TerrainChunk>() == null || h.distance >= best) continue;
                best = h.distance;
                point = h.point;
                found = true;
            }
            return found;
        }

        /// <summary>
        /// The reel's velocity this step for a body at `feet` (the planet's g not yet cancelled): toward the hook at the reel speed × `load`,
        /// never past the stop under it; zero once there (the surveyor hangs).
        /// </summary>
        public Vector2 Pull(Vector2 feet, float load, float dt)
        {
            var hands = feet + new Vector2(0f, Ascent.HandsUp);
            var d = Anchor - hands;
            float dist = d.magnitude;
            AtHook = dist <= Ascent.ReelStop;
            if (AtHook) return Vector2.zero;
            float speed = Mathf.Min(Ascent.ReelSpeed * load, (dist - Ascent.ReelStop) / Mathf.Max(1e-4f, dt) + 0.01f);
            return d / dist * speed;
        }

        void FixedUpdate()
        {
            if (!Flying) return;
            flightT += Time.fixedDeltaTime;
            if (flightT < flightFor) return;
            Flying = false;
            if (!FlightHits) return; // a miss: the hook falls back
            Anchor = FlightTo;
            Attached = true;
            AtHook = false;
            Caught++;
        }

        void LateUpdate()
        {
            if ((Attached || Flying) && !held) Release();
            bool show = Attached || Flying;
            if (line.enabled != show) line.enabled = show;
            if (hook.enabled != (show && hook.sprite != null)) hook.enabled = show && hook.sprite != null;
            if (!show) return;
            Vector2 tip = Flying ? Vector2.Lerp(flightFrom, FlightTo, Mathf.Clamp01(flightT / Mathf.Max(1e-4f, flightFor))) : Anchor;
            if (Flying && Attached) tip = Anchor; // the second hook flies while the first holds: the line stays on the holding one
            Vector2 hands = HandsDrawn();
            var dir = tip - hands;
            if (dir.sqrMagnitude < 1e-6f) dir = Vector2.up;
            dir.Normalize();
            float deg = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg - 90f; // the hook's +y along the throw
            var rot = Quaternion.Euler(0f, 0f, deg);
            hook.transform.SetPositionAndRotation(new Vector3(tip.x, tip.y, 0f), rot);
            var lineEnd = tip + (Vector2)(rot * HookLineSocket);
            line.SetPosition(0, new Vector3(hands.x, hands.y, 0f));
            line.SetPosition(1, new Vector3(lineEnd.x, lineEnd.y, 0f));
        }

        /// <summary>The line's end as drawn: the reel_up frame's reel socket (side_b), else the Grapple's muzzle.</summary>
        Vector2 HandsDrawn()
        {
            var v = tool != null ? tool.Body : null;
            if (v != null && v.Renderer != null && JetpackOverlay.SheetB(v.Renderer.sprite))
            {
                var table = ArtMaterials.SocketFor(Meridian.Art.ArtKeys.Characters.SurveyorSideB, "reel");
                int i = JetpackOverlay.FrameOf(v.Renderer.sprite);
                if (table != null && table.Has(i))
                {
                    bool flip = v.Renderer.flipX;
                    return v.SquashRoot.TransformPoint(new Vector3(flip ? -table[i, 0] : table[i, 0], table[i, 1], 0f));
                }
            }
            return tool != null && tool.Tool != null && tool.Tool.enabled ? tool.MuzzleWorld : Hands;
        }
    }
}
